import json
import re
from typing import List
from app.schemas.claim import Claim
from app.services.model_client import ModelClient


def extract_claims(text: str) -> List[Claim]:
    """
    Extract atomic factual claims using LLM via OpenRouter.
    """

    prompt = f"""
    Extract all atomic statements from the following text.

    Rules:
    - Break text into standalone atomic statements.
    - Include factual statements, opinions, and predictions.
    - Each statement must be self-contained.
    - Do not merge multiple ideas into one.
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
        raise Exception("No JSON object found in model response")

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
            return [Claim(text=t) for t in cleaned]

    claims_data = parsed.get("claims", [])
    return [Claim(text=c.get("text", "").strip()) for c in claims_data if isinstance(c, dict) and c.get("text")]