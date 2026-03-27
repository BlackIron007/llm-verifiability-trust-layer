import re
from app.services.nli_service import check_claim_evidence_support_batch
from app.services.embedding_service import compute_similarity
from app.modules.coreference_resolver import _extract_named_entities
from app.schemas.claim import VerificationStatus

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
    numbers_as_strings = re.findall(r'\b\d[\d,.]*\b', text)
    normalized_numbers = []
    for num_str in numbers_as_strings:
        try:
            normalized_numbers.append(float(num_str.replace(',', '')))
        except ValueError:
            continue
    return normalized_numbers

def detect_internal_contradictions(claims):
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

            numbers_a = _extract_and_normalize_numbers(claim_a)
            numbers_b = _extract_and_normalize_numbers(claim_b)
            
            if numbers_a and numbers_b and set(numbers_a) != set(numbers_b):
                text_a_no_nums = re.sub(r'\b\d[\d,.]*\b', '[NUM]', claim_a)
                text_b_no_nums = re.sub(r'\b\d[\d,.]*\b', '[NUM]', claim_b)

                if compute_similarity(text_a_no_nums, text_b_no_nums) > 0.95:
                    contradictions.append({
                        "claim_a": claim_a,
                        "claim_b": claim_b,
                        "confidence": 0.95,
                        "type": "numeric_rule"
                    })
                    claim_a_obj.verification_status = VerificationStatus.CONTRADICTED
                    claim_b_obj.verification_status = VerificationStatus.CONTRADICTED
                    contradicted_indices.add(i)
                    contradicted_indices.add(j)
                    continue

            subj_a, attr_a = _get_subject_and_attribute(claim_a)
            subj_b, attr_b = _get_subject_and_attribute(claim_b)

            if subj_a and attr_a and subj_b and attr_b:
                if compute_similarity(subj_a, subj_b) > 0.9:
                    if ANTONYMS.get(attr_a.lower()) == attr_b.lower():
                        contradictions.append({
                            "claim_a": claim_a,
                            "claim_b": claim_b,
                            "confidence": 0.98,
                            "type": "antonym_rule"
                        })
                        claim_a_obj.verification_status = VerificationStatus.CONTRADICTED
                        claim_b_obj.verification_status = VerificationStatus.CONTRADICTED
                        contradicted_indices.add(i)
                        contradicted_indices.add(j)
                        continue

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
                similarity = compute_similarity(claim_a, claim_b)
            except Exception:
                similarity = 0.0

            if similarity < SIMILARITY_THRESHOLD:
                continue
            
            pairs_to_check.append((claim_a, claim_b))
            original_pairs_meta.append({'i': i, 'j': j, 'claim_a_text': claim_a, 'claim_b_text': claim_b})

    if not pairs_to_check:
        return contradictions

    results = check_claim_evidence_support_batch(pairs_to_check)

    for i, (label, score) in enumerate(results):
        if label == "contradicts" and score > CONTRADICTION_CONFIDENCE:
            meta = original_pairs_meta[i]
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
                claims[meta['j']].verification_status = VerificationStatus.CONTRADICTED
                contradicted_indices.add(meta['i'])
                contradicted_indices.add(meta['j'])

    return contradictions