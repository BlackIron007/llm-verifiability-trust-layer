import re
from app.services.nli_service import check_claim_evidence_support_batch
from app.services.embedding_service import compute_similarity
from app.schemas.claim import VerificationStatus
from app.services.global_cache import embedding_cache, nli_cache
import logging

QUALIFIER_PHRASES_FOR_CONTRADICTION = {
    "at sea level", "in a vacuum", "on earth", "on mars", "at room temperature",
    "under normal conditions", "in the northern hemisphere", "in the southern hemisphere",
    "during the day", "at night", "at high altitude"
}

logger = logging.getLogger("verifier")

QUALIFIER_REGEX = re.compile(r'\b(' + '|'.join(re.escape(q) for q in QUALIFIER_PHRASES_FOR_CONTRADICTION) + r')\b', re.IGNORECASE)

NUMERIC_REGEX = re.compile(r'\b\d[\d,.]*\b')

ANTONYMS = {
    "flat": "round", "round": "flat",
    "hot": "cold", "cold": "hot",
    "fast": "slow", "slow": "fast",
    "big": "small", "small": "big",
    "large": "small",
    "light": "dark", "dark": "light",
    "light": "heavy", "heavy": "light",
    "right": "wrong", "wrong": "right",
    "true": "false", "false": "true",
    "open": "closed", "closed": "open",
    "on": "off", "off": "on",
    "up": "down", "down": "up",
}

WORLD_KNOWLEDGE_CONTRADICTIONS = {
    "einstein": ["internet", "computer", "phone"],
    "napoleon": ["usa", "america", "airplane", "car"],
    "shakespeare": ["movie", "film", "television"],
    "columbus": ["australia"]
}

def _get_subject_and_attribute(text: str):
    """
    Very simple NLP to split 'Subject is Attribute' style claims.
    e.g., 'The Earth is round' -> ('The Earth', 'round')
    """
    match = re.search(r'\b(is|are|was|were)\b', text, re.IGNORECASE)
    if not match:
        return None, None
    
    subject = text[:match.start()].strip()
    attribute = text[match.end():].strip().rstrip('.')
    return subject, attribute

def _extract_and_normalize_numbers(text: str) -> list[float]:
    """Extracts numeric values from a string and normalizes them to floats."""
    numbers_as_strings = NUMERIC_REGEX.findall(text)
    normalized_numbers = []
    for num_str in numbers_as_strings:
        try:
            normalized_numbers.append(float(num_str.replace(',', '')))
        except ValueError:
            continue
    return normalized_numbers

def _normalize_for_numeric_check(text: str) -> str:
    """Removes numbers and known qualifiers to compare the base statement."""
    text_no_nums = NUMERIC_REGEX.sub('[NUM]', text)
    text_no_qualifiers = QUALIFIER_REGEX.sub('', text_no_nums)
    return re.sub(r'\s+', ' ', text_no_qualifiers).strip()

def detect_internal_contradictions(claims, mode="full"):
    """
    Detect contradictions between claims within the same answer.
    Uses both rule-based checks and NLI for broader coverage.
    If a contradiction is found, it marks both claims.
    """
    contradictions = []
    contradicted_indices = set()

    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            if i in contradicted_indices or j in contradicted_indices:
                continue

            claim_a_obj = claims[i]
            claim_b_obj = claims[j]
            claim_a = claim_a_obj.resolved_text or claim_a_obj.text
            claim_b = claim_b_obj.resolved_text or claim_b_obj.text

            subj_a, attr_a = _get_subject_and_attribute(claim_a)
            subj_b, attr_b = _get_subject_and_attribute(claim_b)

            numbers_a = _extract_and_normalize_numbers(claim_a)
            numbers_b = _extract_and_normalize_numbers(claim_b)
            
            if numbers_a and numbers_b and set(numbers_a) != set(numbers_b):
                subjects_are_similar = False
                if subj_a and subj_b:
                    cache_key = hash(frozenset({subj_a, subj_b}))
                    if cache_key not in embedding_cache:
                        embedding_cache[cache_key] = compute_similarity(subj_a, subj_b)
                    if embedding_cache[cache_key] > 0.9:
                        subjects_are_similar = True

                if subjects_are_similar or (subj_a and subj_b and subj_b.lower() in {"it", "he", "she", "they"} and j == i + 1):
                    logger.info(f"Numeric contradiction found by subject grouping: '{claim_a}' vs '{claim_b}'")
                    contradictions.append({
                        "claim_a": claim_a, "claim_b": claim_b, "confidence": 1.0, "type": "numeric_heuristic"
                    })
                    claim_a_obj.verification_status = VerificationStatus.CONTRADICTED
                    claim_a_obj.contradiction_strength = 1.0
                    claim_b_obj.verification_status = VerificationStatus.CONTRADICTED
                    claim_b_obj.contradiction_strength = 1.0
                    contradicted_indices.add(i)
                    contradicted_indices.add(j)
                    continue

            if subj_a and attr_a and subj_b and attr_b:
                cache_key = hash(frozenset({subj_a, subj_b}))
                if cache_key not in embedding_cache:
                    embedding_cache[cache_key] = compute_similarity(subj_a, subj_b)
                subject_similarity = embedding_cache[cache_key]

                if subject_similarity > 0.9:
                    if ANTONYMS.get(attr_a.lower()) == attr_b.lower():
                        logger.info(f"Antonym contradiction found: '{claim_a}' vs '{claim_b}'")
                        contradictions.append({
                            "claim_a": claim_a,
                            "claim_b": claim_b,
                            "confidence": 0.98,
                            "type": "antonym_rule"
                        })
                        claim_a_obj.verification_status = VerificationStatus.CONTRADICTED
                        claim_a_obj.contradiction_strength = 1.0
                        claim_b_obj.verification_status = VerificationStatus.CONTRADICTED
                        claim_b_obj.contradiction_strength = 1.0
                        contradicted_indices.add(i)
                        contradicted_indices.add(j)
                        continue

    if mode == "rules_only":
        return contradictions

    SIMILARITY_THRESHOLD = 0.85
    CONTRADICTION_CONFIDENCE = 0.7

    pairs_to_check = []
    original_pairs_meta = []

    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            if i in contradicted_indices or j in contradicted_indices:
                continue

            claim_a_obj = claims[i]
            claim_b_obj = claims[j]
            claim_a = claim_a_obj.resolved_text or claim_a_obj.text
            claim_b = claim_b_obj.resolved_text or claim_b_obj.text

            try:
                cache_key = hash(frozenset({claim_a, claim_b}))
                if cache_key not in embedding_cache:
                    embedding_cache[cache_key] = compute_similarity(claim_a, claim_b)
                similarity = embedding_cache[cache_key]
            except Exception as e:
                logger.error(f"Error computing similarity in contradiction check: {e}")
                similarity = 0.0

            if similarity < SIMILARITY_THRESHOLD:
                continue
            
            pairs_to_check.append((claim_a, claim_b))
            original_pairs_meta.append({'i': i, 'j': j, 'claim_a_text': claim_a, 'claim_b_text': claim_b})

    if not original_pairs_meta:
        return contradictions

    nli_batch_pairs = []
    nli_batch_meta = []
    for meta in original_pairs_meta:
        claim_a = meta['claim_a_text']
        claim_b = meta['claim_b_text']
        cache_key = hash((claim_a, claim_b))
        if cache_key in nli_cache:
            label, score = nli_cache[cache_key]
            if label == "contradicts" and score > CONTRADICTION_CONFIDENCE:
                _mark_contradiction(claims, meta, score, contradictions, contradicted_indices)
        else:
            nli_batch_pairs.append((claim_a, claim_b))
            nli_batch_meta.append(meta)

    if nli_batch_pairs:
        results = check_claim_evidence_support_batch(nli_batch_pairs)
        for i, (label, score) in enumerate(results):
            pair = nli_batch_pairs[i]
            cache_key = hash((pair[0], pair[1]))
            nli_cache[cache_key] = (label, score)
            
            meta = nli_batch_meta[i]
            if label == "contradicts" and score > CONTRADICTION_CONFIDENCE:
                _mark_contradiction(claims, meta, score, contradictions, contradicted_indices)

    return contradictions

def _mark_contradiction(claims, meta, score, contradictions, contradicted_indices):
    """Helper function to mark claims as contradicted."""
    claim_a_text = meta['claim_a_text']
    claim_b_text = meta['claim_b_text']
    
    if claim_a_text and claim_b_text:
        contradictions.append({
            "claim_a": claim_a_text,
            "claim_b": claim_b_text,
            "confidence": round(score, 3),
            "type": "nli"
        })
        claims[meta['i']].verification_status = VerificationStatus.CONTRADICTED
        claims[meta['i']].contradiction_strength = round(score, 3)
        claims[meta['j']].verification_status = VerificationStatus.CONTRADICTED
        claims[meta['j']].contradiction_strength = round(score, 3)
        contradicted_indices.add(meta['i'])
        contradicted_indices.add(meta['j'])

def check_world_knowledge_contradictions(claims: list) -> list:
    """
    Checks individual claims against a small, high-confidence blacklist of anachronisms
    or impossible combinations.
    """
    for claim in claims:
        if claim.verification_status == VerificationStatus.CONTRADICTED:
            continue

        text_lower = (claim.resolved_text or claim.text).lower()

        for entity, impossible_keywords in WORLD_KNOWLEDGE_CONTRADICTIONS.items():
            if entity in text_lower:
                for keyword in impossible_keywords:
                    if keyword in text_lower:
                        logger.info(f"World knowledge contradiction found for claim: '{claim.text}' (entity: {entity}, keyword: {keyword})")
                        claim.verification_status = VerificationStatus.CONTRADICTED
                        claim.contradiction_strength = 1.0
                        break
            if claim.verification_status == VerificationStatus.CONTRADICTED:
                break
    return claims