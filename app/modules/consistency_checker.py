from app.services.embedding_service import compute_similarity
from app.modules.coreference_resolver import _extract_named_entities
from app.services.global_cache import embedding_cache
import re

def check_question_claim_consistency(question: str, claim_text: str):
    """
    Check whether the claim actually answers the question.
    """

    try:
        cache_key = hash(frozenset({question, claim_text}))
        if cache_key not in embedding_cache:
            embedding_cache[cache_key] = compute_similarity(question, claim_text)
        similarity = embedding_cache[cache_key]
    except Exception:
        similarity = 0.0

    q_entities = set(_extract_named_entities(question))
    c_entities = set(_extract_named_entities(claim_text))
    if q_entities and c_entities and q_entities.intersection(c_entities):
        if similarity > 0.6:
            similarity += 0.2
    
    q_years = set(re.findall(r'\b(?:1[0-9]{3}|20[0-2][0-9])\b', question))
    c_years = set(re.findall(r'\b(?:1[0-9]{3}|20[0-2][0-9])\b', claim_text))
    if q_years and c_years:
        if not q_years.intersection(c_years):
            approx_match = False
            for qy in q_years:
                for cy in c_years:
                    if abs(int(qy) - int(cy)) <= 10:
                        approx_match = True
                        break
            if approx_match:
                similarity -= 0.2
            else:
                similarity -= 0.5

    similarity = max(0.0, min(1.0, similarity))

    if similarity < 0.35:
        return False, similarity

    return True, similarity