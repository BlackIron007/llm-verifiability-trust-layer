from app.schemas.claim import Claim, ClaimType, VerificationStatus
from app.services.model_client import ModelClient
from app.modules.risk_scorer import compute_risk_level
from app.services.embedding_service import compute_similarity
from app.services.explanation_analyzer import information_density
import re
import json

VAGUE_WORDS = {
    "rapidly", "better", "improving", "growing", "many", "often", "some", "most",
    "frequently", "generally", "usually", "significant", "substantial", "good", "bad"
}

def _is_claim_vague(claim_text: str) -> bool:
    """
    Detects if a claim is vague by checking for subjective/trend words
    and a lack of measurable metrics (numbers).
    """
    if re.search(r'\d', claim_text):
        return False

    for word in VAGUE_WORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', claim_text, re.IGNORECASE):
            return True

    return False

def rephrase_claim(claim_text: str) -> str:
    """
    Ask the model to rephrase the claim without changing meaning.
    """

    prompt = f"""
    Rephrase the following claim without adding new context.

    Rules:
    - Keep the meaning identical
    - Do not introduce assumptions
    - Do not specify events that are not mentioned
    - Do not expand the claim
    - Return only the rewritten sentence

    Claim:
    \"\"\"{claim_text}\"\"\"
    """

    from app.services.global_cache import llm_cache
    cache_key = hash(prompt)
    if cache_key in llm_cache:
        return llm_cache[cache_key]
    
    response = ModelClient.generate(prompt).strip()
    llm_cache[cache_key] = response
    return response

def refine_verifiability(claim: Claim) -> Claim:
    """
    Refines verifiability score, including checks for vague claims that cannot be fact-checked.
    """

    if claim.claim_type not in {ClaimType.HARD_FACT, ClaimType.SOFT_FACT}:
        return claim

    if _is_claim_vague(claim.text):
        claim.verifiability_score = 0.75
        claim.verification_status = VerificationStatus.UNVERIFIABLE
        claim.explanation = "Claim contains subjective language without a measurable metric, making it unverifiable."
        claim.risk_level = compute_risk_level(claim.verifiability_score)
        return claim

    if claim.verifiability_score is not None:
        claim.verifiability_score = round(claim.verifiability_score, 3)
        claim.risk_level = compute_risk_level(claim.verifiability_score)

    claim.explanation = ""
    claim.secondary_explanation = ""
    claim.tertiary_explanation = ""

    return claim