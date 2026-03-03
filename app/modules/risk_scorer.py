from typing import List
from app.schemas.claim import Claim, ClaimType, RiskLevel

BASE_RISK_MAP = {
    ClaimType.HARD_FACT: 0.7,
    ClaimType.SOFT_FACT: 0.5,
    ClaimType.PREDICTION: 0.6,
    ClaimType.OPINION: 0.2
}

def assign_baseline_risk(claim: Claim) -> Claim:
    """
    Assigns baseline verifiability score and risk level
    based on claim type.
    """

    if claim.claim_type is None:
        return claim

    base_score = BASE_RISK_MAP.get(claim.claim_type, 0.5)
    claim.verifiability_score = base_score

    if base_score >= 0.65:
        claim.risk_level = RiskLevel.HIGH
    elif base_score >= 0.4:
        claim.risk_level = RiskLevel.MEDIUM
    else:
        claim.risk_level = RiskLevel.LOW

    return claim

def compute_overall_trust_score(claims: List[Claim]) -> float:
    """
    Compute overall trust score as inverse average risk.
    Higher trust score = lower average risk.
    """

    if not claims:
        return 1.0

    avg_risk = sum(c.verifiability_score or 0 for c in claims) / len(claims)

    trust_score = 1 - avg_risk

    return round(trust_score, 3)