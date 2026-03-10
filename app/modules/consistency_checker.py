from app.services.embedding_service import compute_similarity

def check_question_claim_consistency(question: str, claim_text: str):
    """
    Check whether the claim actually answers the question.
    """

    try:
        similarity = compute_similarity(question, claim_text)
    except Exception:
        similarity = 0.0

    if similarity < 0.35:
        return False, similarity

    return True, similarity