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
    Detects contradictions between claims. A single-pass approach for efficiency.
    1. It first checks for high-confidence, rule-based contradictions (numeric, antonyms).
    2. If no rule-based contradiction is found and mode is 'full', it prepares pairs for NLI.
    3. Finally, it runs a batch NLI check on the remaining candidate pairs.
    """
    contradictions = []
    contradicted_indices = set()
    
    pairs_for_nli = []
    meta_for_nli = []

    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            if i in contradicted_indices or j in contradicted_indices:
                continue

            claim_a_obj = claims[i]
            claim_b_obj = claims[j]
            claim_a = claim_a_obj.resolved_text or claim_a_obj.text
            claim_b = claim_b_obj.resolved_text or claim_b_obj.text

            rule_contradiction_found = False

            subj_a, _ = _get_subject_and_attribute(claim_a)
            subj_b, _ = _get_subject_and_attribute(claim_b)
            numbers_a = _extract_and_normalize_numbers(claim_a)
            numbers_b = _extract_and_normalize_numbers(claim_b)
            if numbers_a and numbers_b and set(numbers_a) != set(numbers_b):
                is_pronoun_ref = (subj_a and subj_b and subj_b.lower() in {"it", "he", "she", "they"} and j == i + 1)
                base_a = _normalize_for_numeric_check(claim_a)
                base_b = _normalize_for_numeric_check(claim_b)
                cache_key = hash(frozenset({base_a, base_b}))
                if cache_key not in embedding_cache:
                    embedding_cache[cache_key] = compute_similarity(base_a, base_b)
                if embedding_cache.get(cache_key, 0) > 0.95 or is_pronoun_ref:
                    logger.info(f"Numeric contradiction found: '{claim_a}' vs '{claim_b}'")
                    _mark_contradiction(claims, {'i': i, 'j': j, 'claim_a_text': claim_a, 'claim_b_text': claim_b}, 1.0, contradictions, contradicted_indices)
                    rule_contradiction_found = True
            
            if rule_contradiction_found: continue

            subj_a, attr_a = _get_subject_and_attribute(claim_a)
            subj_b, attr_b = _get_subject_and_attribute(claim_b)
            if subj_a and attr_a and subj_b and attr_b:
                cache_key = hash(frozenset({subj_a, subj_b}))
                if cache_key not in embedding_cache:
                    embedding_cache[cache_key] = compute_similarity(subj_a, subj_b)
                if embedding_cache.get(cache_key, 0) > 0.9 and ANTONYMS.get(attr_a.lower()) == attr_b.lower():
                    logger.info(f"Antonym contradiction found: '{claim_a}' vs '{claim_b}'")
                    _mark_contradiction(claims, {'i': i, 'j': j, 'claim_a_text': claim_a, 'claim_b_text': claim_b}, 0.98, contradictions, contradicted_indices)
                    rule_contradiction_found = True

            if rule_contradiction_found: continue

            if mode == "full":
                if numbers_a and numbers_b and set(numbers_a) != set(numbers_b):
                    continue
                
                try:
                    cache_key = hash(frozenset({claim_a, claim_b}))
                    if cache_key not in embedding_cache:
                        embedding_cache[cache_key] = compute_similarity(claim_a, claim_b)
                    similarity = embedding_cache[cache_key]
                except Exception as e:
                    logger.error(f"Error computing similarity for NLI check: {e}")
                    similarity = 0.0
                
                if similarity >= 0.95:
                    pairs_for_nli.append((claim_a, claim_b))
                    meta_for_nli.append({'i': i, 'j': j, 'claim_a_text': claim_a, 'claim_b_text': claim_b})

    if pairs_for_nli:
        logger.info(f"Checking {len(pairs_for_nli)} pairs for NLI contradiction.")
        
    nli_batch_pairs = []
    nli_batch_meta = []
    for i, pair in enumerate(pairs_for_nli):
        cache_key = hash(pair)
        if cache_key in nli_cache:
            label, score = nli_cache[cache_key]
            if label == "contradicts" and score > 0.9:
                _mark_contradiction(claims, meta_for_nli[i], score, contradictions, contradicted_indices)
        else:
            nli_batch_pairs.append(pair)
            nli_batch_meta.append(meta_for_nli[i])

    if nli_batch_pairs:
        results = check_claim_evidence_support_batch(nli_batch_pairs)
        for i, (label, score) in enumerate(results):
            pair = nli_batch_pairs[i]
            cache_key = hash(pair)
            nli_cache[cache_key] = (label, score)
            
            meta = nli_batch_meta[i]
            if label == "contradicts" and score > 0.9:
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