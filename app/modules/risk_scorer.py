from typing import List
from app.schemas.claim import Claim, ClaimType, RiskLevel, VerificationStatus

BASE_RISK_MAP = {
    ClaimType.HARD_FACT: 0.3,
    ClaimType.SOFT_FACT: 0.5,
    ClaimType.PREDICTION: 0.7,
    ClaimType.OPINION: 0.2
}

import re

def assign_baseline_risk(claim: Claim) -> Claim:
    """
    Assigns baseline verifiability score and risk level
    based on claim type.
    """

    if claim.claim_type is None:
        return claim

    base_score = BASE_RISK_MAP.get(claim.claim_type, 0.5)

    if claim.claim_type == ClaimType.HARD_FACT and re.search(r'\b\d{3,}\b', claim.text):
        base_score = max(0.1, base_score - 0.15)

    claim.verifiability_score = base_score

    claim.risk_level = compute_risk_level(base_score)

    return claim

def compute_risk_level(score: float) -> RiskLevel:
    """
    Convert numeric uncertainty score into categorical risk level.
    """

    if score >= 0.65:
        return RiskLevel.HIGH
    elif score >= 0.4:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW

def compute_overall_trust_score(claims: List[Claim]) -> float:
    """
    Computes an overall trust score based on the verification status of all claims.
    This logic is designed to be robust and intuitive.
    """

    if not claims:
        return 1.0

    num_claims = len(claims)
    num_contradicted = sum(1 for c in claims if c.verification_status == VerificationStatus.CONTRADICTED)
    num_supported = sum(1 for c in claims if c.verification_status == VerificationStatus.SUPPORTED)
    num_unverifiable = sum(1 for c in claims if c.verification_status == VerificationStatus.UNVERIFIABLE)

    if num_contradicted > 0:
        return max(0.1, 0.5 - (num_contradicted / num_claims) * 0.4)

    if num_unverifiable == num_claims:
        return 0.5

    score = 1.0

    num_unsupported = num_claims - num_supported - num_unverifiable - num_contradicted
    
    unsupported_penalty = (num_unsupported / num_claims) * 0.5
    unverifiable_penalty = (num_unverifiable / num_claims) * 0.25

    score = score - unsupported_penalty - unverifiable_penalty

    return round(max(0.0, score), 3)