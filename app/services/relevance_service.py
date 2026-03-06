from app.services.embedding_service import compute_similarity

def compute_qa_relevance(question: str, answer: str) -> float:
    """
    Computes semantic relevance between the user question
    and the LLM answer using embedding similarity.
    """

    similarity = compute_similarity(question, answer)

    relevance_score = max(0.0, min(similarity, 1.0))

    return round(relevance_score, 3)