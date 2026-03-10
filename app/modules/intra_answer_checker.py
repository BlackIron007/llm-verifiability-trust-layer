from app.services.nli_service import check_claim_evidence_support

def detect_internal_contradictions(claims):
    """
    Detect contradictions between claims within the same answer.
    """

    contradictions = []

    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):

            claim_a = claims[i].text
            claim_b = claims[j].text

            label, score = check_claim_evidence_support(claim_a, claim_b)

            if label == "contradicts" and score > 0.7:
                contradictions.append({
                    "claim_a": claim_a,
                    "claim_b": claim_b,
                    "confidence": round(score, 3)
                })

    return contradictions