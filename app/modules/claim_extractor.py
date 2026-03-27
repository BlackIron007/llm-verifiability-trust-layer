import json
import re
from typing import List
from app.schemas.claim import Claim
from app.services.model_client import ModelClient

META_PHRASES = (
    "Here is the atomic statement",
    "Here are the atomic statements",
    "This statement is",
    "The quote is",
    "I am",
    "I'm",
    "As an AI",
    "The atomic statement",
    "This is a tautology",
    "The statement is a complete factual unit",
)

HEDGING_PHRASES = (
    "maybe", "perhaps", "possibly", "probably", "might be", "could be", "seems to",
    "in my opinion", "i think", "i believe"
)


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


def _strip_outer_quotes(s: str) -> str:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1].strip()
    return s


def _is_meta_statement(s: str) -> bool:
    lower = s.lower()
    if any(phrase.lower() in lower for phrase in META_PHRASES):
        return True
    if re.match(r"^(here is|here are|this statement|the quote|note:|explanation:|analysis:|reasoning:|justification:)\b", lower):
        return True
    return False


def _is_hedged(s: str) -> bool:
    lower = s.lower()
    return any(phrase in lower for phrase in HEDGING_PHRASES)


def filter_claims(claims: List[Claim]) -> List[Claim]:
    """Sanitize and remove fragments/meta/instructional statements."""
    filtered: List[Claim] = []
    for c in claims:
        text = _strip_outer_quotes((c.text or "").strip())
        if not text:
            continue
        if len(text.split()) < 3:
            continue
        if text.lower().startswith(("in ", "on ", "at ", "during ", "after ", "before ")):
            continue
        if _is_meta_statement(text):
            continue
        if _is_hedged(text):
            continue
        c.text = text
        filtered.append(c)
    return filtered


def extract_claims(text: str) -> List[Claim]:
    """
    Extract atomic factual claims using LLM via OpenRouter.
    """

    prompt = f'''You are a precise claim extractor. Extract only atomic, declarative statements from the provided Text. Do not add explanations, headings, or meta commentary.

Rules (critical):
- Each claim MUST be a single, self-contained factual statement that preserves modifiers that change truth conditions (dates, locations, quantities, names). Do NOT split such modifiers.
  Example: Correct -> "India became independent in 1947" (ONE claim). Incorrect -> "India became independent" / "in 1947".
- CRITICAL: DO NOT remove temporal modifiers like "later", "earlier", "eventually", "subsequently", "recently", "currently". Preserve the EXACT original wording as much as possible.
- Do NOT include instructions, descriptions about statements, or quotes introducing a statement (e.g., "Here is the atomic statement...").
- Do NOT include questions, imperatives, or meta text about the task.
- Output strictly valid JSON. Do not include any text before or after JSON.

Format:
{{
  "claims": [
    {{"text": "statement 1"}},
    {{"text": "statement 2"}}
  ]
}}

Text:
"""{text}"""
'''

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

    seen = set()
    deduped: List[Claim] = []
    for c in claims:
        key = c.text.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    return deduped