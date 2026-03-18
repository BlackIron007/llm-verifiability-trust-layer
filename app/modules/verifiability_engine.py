from app.schemas.claim import Claim, ClaimType
from app.services.model_client import ModelClient
from app.modules.risk_scorer import compute_risk_level
from app.services.embedding_service import compute_similarity
from app.services.explanation_analyzer import information_density
import re
import json

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

    return ModelClient.generate(prompt).strip()

def refine_verifiability(claim: Claim) -> Claim:
    """
    Refines verifiability score. In this version, LLM-based explanation generation
    is disabled to meet latency targets for a real-time API.
    """

    if claim.claim_type not in {ClaimType.HARD_FACT, ClaimType.SOFT_FACT}:
        return claim

    if claim.verifiability_score is not None:
        claim.verifiability_score = round(claim.verifiability_score, 3)
        claim.risk_level = compute_risk_level(claim.verifiability_score)

    claim.explanation = ""
    claim.secondary_explanation = ""
    claim.tertiary_explanation = ""

    return claim