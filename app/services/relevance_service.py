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

    if similarity >= 0.5:
        relevance_score = 0.95
    elif similarity >= 0.3:
        relevance_score = 0.7
    else:
        relevance_score = max(0.0, similarity)

    return round(relevance_score, 3)