from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

def compute_similarity(text_a: str, text_b: str) -> float:
    """
    Compute semantic similarity between two texts.
    Returns value between 0 and 1.
    """

    embeddings = model.encode([text_a, text_b])

    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    return float(similarity)