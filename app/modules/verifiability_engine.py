from app.schemas.claim import Claim, ClaimType
from app.services.model_client import ModelClient
from app.modules.risk_scorer import compute_risk_level
from app.services.embedding_service import compute_similarity
from app.services.explanation_analyzer import information_density
import re
import json

def refine_verifiability(claim: Claim) -> Claim:
    """
    Refines verifiability score by checking explanation stability.
    Applies only to factual claims.
    """

    if claim.claim_type not in {ClaimType.HARD_FACT, ClaimType.SOFT_FACT}:
        return claim

    explanation_prompt = f"""
    Provide a concise factual explanation supporting the claim.

    Rules:
    - Do not include introductory phrases.
    - Do not say "here is an explanation".
    - Respond with the explanation only.
    - Maximum 120 words.

    Claim:
    \"\"\"{claim.text}\"\"\"
    """

    explanation_1 = ModelClient.generate(explanation_prompt)

    explanation_prompt_2 = f"""
    Briefly justify the historical or factual basis of this statement:
    
    Rules:
    - Do not include introductory phrases.
    - Do not say "here is an explanation".
    - Respond with the explanation only.
    - Maximum 120 words.    

    \"\"\"{claim.text}\"\"\"
    """

    explanation_2 = ModelClient.generate(explanation_prompt_2)

    similarity = compute_similarity(explanation_1, explanation_2)
    instability_score = 1 - similarity
    
    density = information_density(explanation_1)
    if density < 0.55:
        claim.verifiability_score = min(
            claim.verifiability_score + 0.1,
            1.0
        )

    if claim.verifiability_score is not None:
        claim.verifiability_score = round(
            min(claim.verifiability_score + instability_score * 0.15, 1.0),
            3
        )
        claim.risk_level = compute_risk_level(claim.verifiability_score)

    claim.explanation = explanation_1.strip()
    claim.secondary_explanation = explanation_2.strip()

    return claim