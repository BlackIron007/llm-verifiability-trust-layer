from app.services.embedding_service import compute_similarity
from app.services.global_cache import embedding_cache

def compute_qa_relevance(question: str, answer: str) -> float:
    """
    Computes semantic relevance between the user question
    and the LLM answer using embedding similarity.
    """
    cache_key = hash(frozenset({question, answer}))
    if cache_key in embedding_cache:
        similarity = embedding_cache[cache_key]
    else:
        similarity = compute_similarity(question, answer)
        embedding_cache[cache_key] = similarity

    relevance_score = max(0.0, min(similarity, 1.0))

    return round(relevance_score, 3)