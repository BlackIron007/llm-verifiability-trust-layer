from typing import List
from app.schemas.claim import Claim, ClaimType, RiskLevel

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

    if claim.claim_type == ClaimType.HARD_FACT and re.search(r'\b(?:1[0-9]{3}|20[0-2][0-9])\b', claim.text):
        base_score = max(base_score, 0.5)

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
    Evidence-based trust scoring with exponential penalty for multiple bad claims.

    For each claim:
      - trust = support_strength - contradiction_strength, clamped to [0.05, 1.0]
      - If no strong support (support_strength < 0.3), cap trust at 0.15
      - If contradiction detected (contradiction_strength > 0.3), cap trust at 0.1

    Overall trust = product of all per-claim trusts (exponential penalty).
    This ensures multiple incorrect claims compound to very low scores.
    """

    if not claims:
        return 1.0

    per_claim_trusts = []

    for c in claims:
        support = c.support_strength or 0.0
        contradiction = c.contradiction_strength or 0.0

        if c.claim_type == ClaimType.OPINION:
            per_claim_trusts.append(0.8)
            continue

        claim_trust = support - contradiction
        claim_trust = max(0.05, min(1.0, claim_trust))

        if contradiction > 0.3:
            claim_trust = min(claim_trust, 0.1)

        if support < 0.3:
            claim_trust = min(claim_trust, 0.15)

        per_claim_trusts.append(claim_trust)

    if not per_claim_trusts:
        return 1.0

    overall = 1.0
    for t in per_claim_trusts:
        overall *= t
    n = len(per_claim_trusts)
    overall = overall ** (1.0 / n) if n > 1 else overall

    return round(max(0.0, min(1.0, overall)), 3)