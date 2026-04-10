from app.schemas.claim import Claim, ClaimType
from app.services.model_client import ModelClient
import json
import re
from app.services.global_cache import claim_classification_cache, llm_cache
import logging

from transformers import pipeline
import torch

logger = logging.getLogger("verifier")

try:
    CLASSIFIER_PIPELINE = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=0 if torch.cuda.is_available() else -1
    )
    logger.info("Zero-shot classification pipeline loaded successfully for claim classification.")
except Exception as e:
    logger.error(f"Failed to load zero-shot classification pipeline, will fallback to LLM. Error: {e}")
    CLASSIFIER_PIPELINE = None

CANDIDATE_LABELS = ["objective measurable fact", "interpretive or causal statement", "subjective judgment", "statement about the future"]
LABEL_MAP = {
    "objective measurable fact": ClaimType.HARD_FACT,
    "interpretive or causal statement": ClaimType.SOFT_FACT,
    "subjective judgment": ClaimType.OPINION,
    "statement about the future": ClaimType.PREDICTION,
}

def _classify_claim_with_llm(claim: Claim) -> Claim:
    """
    Fallback classification using an external LLM.
    """
    logger.warning(f"Using LLM fallback for claim classification: '{claim.text}'")
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

    cache_key = hash(prompt)
    if cache_key in llm_cache:
        raw_response = llm_cache[cache_key]
    else:
        raw_response = ModelClient.generate(prompt)
        llm_cache[cache_key] = raw_response

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

    return claim

def classify_claim(claim: Claim) -> Claim:
    """
    Classifies a claim using a local zero-shot model for speed, with an LLM fallback.
    Utilizes a cache to avoid re-classifying known claims.
    """

    cache_key = hash(claim.text)
    if cache_key in claim_classification_cache:
        logger.info(f"Claim classification cache hit for: '{claim.text}'")
        claim.claim_type = claim_classification_cache[cache_key]
        return claim
    
    logger.info(f"Claim classification cache miss for: '{claim.text}'")

    if re.search(r'\d', claim.text):
        claim.claim_type = ClaimType.HARD_FACT
        claim_classification_cache[cache_key] = claim.claim_type
        return claim

    from app.modules.coreference_resolver import _extract_named_entities
    if _extract_named_entities(claim.text) and len(claim.text.split()) >= 3:
        claim.claim_type = ClaimType.HARD_FACT
        claim_classification_cache[cache_key] = claim.claim_type
        return claim

    if CLASSIFIER_PIPELINE:
        result = CLASSIFIER_PIPELINE(claim.text, CANDIDATE_LABELS, multi_label=False)
        top_label = result['labels'][0]
        claim.claim_type = LABEL_MAP.get(top_label, ClaimType.SOFT_FACT)
    else:
        claim = _classify_claim_with_llm(claim)

    claim_classification_cache[cache_key] = claim.claim_type

    return claim