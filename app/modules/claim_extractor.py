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

    parsed = json.loads(json_string)
    claims_data = parsed.get("claims", [])

    return [Claim(text=c["text"]) for c in claims_data]