from app.schemas.claim import RiskLevel

def calibrate_claim_trust(claim):
    """
    Adjust claim risk depending on claim type.
    """

    if claim.claim_type == "hard_fact":
        return claim

    if claim.claim_type == "soft_fact":
        claim.verifiability_score *= 0.85

    elif claim.claim_type == "prediction":
        claim.verifiability_score *= 0.7

    elif claim.claim_type == "opinion":
        claim.verifiability_score *= 0.5

    return claim