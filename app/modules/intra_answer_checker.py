from app.services.nli_service import check_claim_evidence_support_batch
from app.services.embedding_service import compute_similarity

def detect_internal_contradictions(claims):
    """
    Detect contradictions between claims within the same answer.
    """

    contradictions = []
    SIMILARITY_THRESHOLD = 0.85
    CONTRADICTION_CONFIDENCE = 0.7

    pairs_to_check = []
    original_pairs = []

    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            claim_a = claims[i].text
            claim_b = claims[j].text

            try:
                similarity = compute_similarity(claim_a, claim_b)
            except Exception:
                similarity = 0.0

            if similarity < SIMILARITY_THRESHOLD:
                continue
            
            pairs_to_check.append((claim_a, claim_b))
            original_pairs.append((claim_a, claim_b))

    if not pairs_to_check:
        return []

    results = check_claim_evidence_support_batch(pairs_to_check)

    for i, (label, score) in enumerate(results):
        if label == "contradicts" and score > CONTRADICTION_CONFIDENCE:
            claim_a, claim_b = original_pairs[i]
            if claim_a and claim_b:
                contradictions.append({
                    "claim_a": claim_a,
                    "claim_b": claim_b,
                    "confidence": round(score, 3)
                })

    return contradictions