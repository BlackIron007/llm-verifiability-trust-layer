import re
from app.modules.coreference_resolver import _extract_named_entities

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "for", "to", "of", "by", "with", "is", "are", "was", "were", "be", "been", "being",
    "he", "she", "it", "they", "i", "you", "we", "his", "her", "its", "their", "my", "your", "our",
    "has", "have", "had", "do", "does", "did", "will", "would", "shall", "should", "can", "could", "may", "might", "must",
    "and", "but", "or", "so", "if", "when", "while", "that", "which", "who", "what", "where", "why", "how",
    "this", "these", "those", "from", "about", "as", "into", "like", "through", "after", "before", "during",
    "rose", "to", "prominence", "became", "developed", "gained", "from", "very"
}

def rewrite_query(claim_text: str) -> str:
    """
    Distills a claim into a concise, keyword-based search query to improve retrieval accuracy and cache hits.
    
    Strategy:
    1. Extract named entities.
    2. Extract numeric values.
    3. Remove stop words and punctuation.
    4. Combine the most salient parts into a query.
    """
    
    entities = _extract_named_entities(claim_text)
    numbers = re.findall(r'\b\d[\d,]*\b', claim_text)
    
    words = re.findall(r'\b\w+\b', claim_text.lower())
    keywords = [word for word in words if word not in STOP_WORDS]
    
    query_parts = list(dict.fromkeys(entities))
    
    seen_words = {word.lower() for ent in entities for word in ent.split()}

    for kw in numbers + keywords:
        if kw not in seen_words:
            query_parts.append(kw)
            seen_words.add(kw)
            
    final_query = " ".join(query_parts)
    
    return final_query if final_query else claim_text