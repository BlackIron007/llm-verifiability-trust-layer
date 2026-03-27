from app.schemas.claim import Claim, ClaimType
from app.services.model_client import ModelClient
import json
import re
from app.services.claim_cache import get_cached_classification, set_cached_classification
import logging

logger = logging.getLogger("verifier")

def classify_claim(claim: Claim) -> Claim:
    """
    Classifies a claim into HARD_FACT, SOFT_FACT, OPINION, or PREDICTION.
    Updates and returns the Claim object.
    Utilizes a cache to avoid re-classifying known claims.
    """

    cached_type = get_cached_classification(claim.text)
    if cached_type is not None:
        logger.info(f"Claim classification cache hit for: '{claim.text}'")
        claim.claim_type = cached_type
        return claim
    
    logger.info(f"Claim classification cache miss for: '{claim.text}'")

    prompt = f"""
    Classify the following claim into one of these categories:

    - hard_fact (objective, measurable, verifiable fact)
    - soft_fact (interpretive or causal factual statement)
    - opinion (subjective judgment or value statement)
    - prediction (statement about the future)

    Return strictly valid JSON in this format:

    {{
        "claim_type": "hard_fact"
    }}

    Claim:
    \"\"\"{claim.text}\"\"\"
    """

    raw_response = ModelClient.generate(prompt)

    json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)

    if not json_match:
        raise Exception("No JSON found in classification response")

    json_string = json_match.group(0)
    parsed = json.loads(json_string)

    claim_type_str = parsed.get("claim_type")

    try:
        claim.claim_type = ClaimType(claim_type_str)
    except Exception:
        claim.claim_type = ClaimType.SOFT_FACT

    from app.modules.coreference_resolver import _extract_named_entities
    entities = _extract_named_entities(claim.text)
    if entities and len(claim.text.split()) > 3:
        claim.claim_type = ClaimType.HARD_FACT

    set_cached_classification(claim.text, claim.claim_type)

    return claim