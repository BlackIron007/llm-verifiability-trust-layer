from app.schemas.claim import Claim, ClaimType
from app.services.model_client import ModelClient
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
    Provide a concise explanation supporting the following claim.

    Claim:
    \"\"\"{claim.text}\"\"\"
    """

    explanation_1 = ModelClient.generate(explanation_prompt)

    explanation_prompt_2 = f"""
    Briefly justify the historical or factual basis of this statement:

    \"\"\"{claim.text}\"\"\"
    """

    explanation_2 = ModelClient.generate(explanation_prompt_2)

    len_diff = abs(len(explanation_1) - len(explanation_2))

    instability_score = min(len_diff / 200, 1.0)

    if claim.verifiability_score is not None:
        claim.verifiability_score = round(
            min(claim.verifiability_score + instability_score * 0.2, 1.0),
            3
        )

    claim.explanation = explanation_1.strip()

    return claim