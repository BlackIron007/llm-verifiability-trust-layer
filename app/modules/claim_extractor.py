import json
import re
from typing import List
from app.schemas.claim import Claim
from app.services.model_client import ModelClient


def repair_split_claims(claims: List[Claim]) -> List[Claim]:
    """
    Merge trailing modifier fragments (e.g., "in 1947", "at New York") into the previous claim.
    This guards against LLMs splitting atomic claims across lines.
    """
    merged: List[Claim] = []
    for c in claims:
        t = (c.text or "").strip()
        if not t:
            continue
        if merged:
            is_short = len(t.split()) < 4
            starts_with_prep = re.match(r"^(in|on|at|during|after|before|by|from|since|until|within|under|over|between|around)\b", t, re.IGNORECASE)
            starts_with_year = re.match(r"^\d{3,4}(\b|\s)", t)
            if is_short and (starts_with_prep or starts_with_year):
                prev = merged[-1]
                prev.text = re.sub(r"[\s.]*$", "", prev.text) + " " + t
                continue
        merged.append(c)
    return merged


def filter_claims(claims: List[Claim]) -> List[Claim]:
    """Remove fragments that are too short or start with leading prepositions."""
    filtered: List[Claim] = []
    for c in claims:
        text = (c.text or "").strip()
        if not text:
            continue
        if len(text.split()) < 2:
            continue
        if text.lower().startswith(("in ", "on ", "at ", "during ", "after ", "before ")):
            continue
        filtered.append(c)
    return filtered


def extract_claims(text: str) -> List[Claim]:
    """
    Extract atomic factual claims using LLM via OpenRouter.
    """

    prompt = f"""
    Extract all atomic statements from the following text.

    Rules (critical):
    - Keep each claim as a complete factual unit that preserves modifiers that change truth conditions
      (dates, locations, quantities, names, constraints). Do NOT split such modifiers onto a new line.
      Example: Correct -> "India became independent in 1947" (ONE claim). Incorrect ->
      "India became independent" / "in 1947" (split into two lines).
    - Break text into standalone atomic statements without merging unrelated ideas.
    - Include factual statements, opinions, and predictions.
    - Each statement must be self-contained and verifiable as-is (no trailing fragments like "in 1947").
    - Return strictly valid JSON.
    - Format:

    {{
        "claims": [
            {{"text": "statement 1"}},
            {{"text": "statement 2"}}
        ]
    }}

    Text:
    \"\"\"{text}\"\"\"
    """

    raw_response = ModelClient.generate(prompt)
    # print("RAW MODEL RESPONSE:")
    # print(raw_response)

    json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
    if not json_match:
        texts = re.findall(r'"text"\s*:\s*"(.*?)"', raw_response, flags=re.DOTALL)
        if not texts:
            candidates = re.split(r'[\r\n]+', raw_response)
            cleaned_list = []
            for t in candidates:
                t = re.sub(r'^[\-\*\d\.)\s]+', '', t).strip()
                if t:
                    cleaned_list.append(t)
        else:
            cleaned_list = [re.sub(r"\\n", " ", t).strip() for t in texts if t.strip()]
        claims = [Claim(text=t) for t in cleaned_list]
        claims = repair_split_claims(claims)
        claims = filter_claims(claims)
        return claims

    json_string = json_match.group(0)

    try:
        parsed = json.loads(json_string)
    except json.JSONDecodeError:
        sanitized = re.sub(r",\s*(\]|\})", r"\\1", json_string)
        try:
            parsed = json.loads(sanitized)
        except json.JSONDecodeError:
            texts = re.findall(r'"text"\s*:\s*"(.*?)"', raw_response, flags=re.DOTALL)
            cleaned = [re.sub(r"\\n", " ", t).strip() for t in texts if t.strip()]
            claims = [Claim(text=t) for t in cleaned]
            claims = repair_split_claims(claims)
            claims = filter_claims(claims)
            return claims

    claims_data = parsed.get("claims", [])
    if not isinstance(claims_data, list):
        return []
    claims = [Claim(text=c.get("text", "").strip()) for c in claims_data if isinstance(c, dict) and c.get("text")]
    claims = repair_split_claims(claims)
    claims = filter_claims(claims)
    return claims