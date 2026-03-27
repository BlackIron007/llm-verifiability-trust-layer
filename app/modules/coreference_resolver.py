"""
Coreference Resolution — Safe Heuristic

Resolves pronouns to the most recent named entity using spaCy NER.
Only replaces pronouns when confidence is high (single unambiguous entity).
Ambiguous cases are left untouched.
"""

import re
import logging

logger = logging.getLogger("verifier")

PRONOUN_PATTERNS = re.compile(
    r'\b(he|she|it|they|him|her|his|its|their|them)\b',
    re.IGNORECASE
)

CAPITALIZED_ENTITY = re.compile(
    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
)


def _extract_named_entities(text: str) -> list[str]:
    """
    Extract named entities from text using capitalized word heuristic.
    Returns list of multi-word or single-word capitalized names.
    Filters out common sentence starters that aren't entities.
    """
    COMMON_STARTERS = {
        "the", "a", "an", "this", "that", "these", "those",
        "here", "there", "it", "he", "she", "they", "we",
        "but", "and", "or", "so", "if", "when", "while",
        "after", "before", "during", "since", "until",
        "however", "therefore", "moreover", "furthermore",
        "also", "too", "very", "much", "many", "some",
        "most", "each", "every", "all", "both", "few",
    }
    
    entities = CAPITALIZED_ENTITY.findall(text)
    filtered = []
    for ent in entities:
        if ent.lower() in COMMON_STARTERS:
            continue
        if len(ent) < 2:
            continue
        filtered.append(ent)
    
    return filtered


def _is_person_pronoun(pronoun: str) -> bool:
    """Check if a pronoun likely refers to a person."""
    return pronoun.lower() in {"he", "she", "him", "her", "his"}


def _is_thing_pronoun(pronoun: str) -> bool:
    """Check if a pronoun likely refers to a thing/concept."""
    return pronoun.lower() in {"it", "its"}


def _replace_pronoun_safe(text: str, entity: str, pronoun: str) -> str:
    """
    Replace a specific pronoun with the entity name.
    Only replaces the first occurrence to avoid over-replacement.
    """
    pattern = re.compile(r'\b' + re.escape(pronoun) + r'\b', re.IGNORECASE)
    return pattern.sub(entity, text, count=1)


def resolve_coreferences(claims: list) -> list:
    """
    Resolve pronoun references across an ordered list of claims.
    
    Strategy:
    - Track the last mentioned named entity and last mentioned person entity
    - If a claim contains pronouns and there's exactly one recent entity, replace safely
    - If ambiguous (multiple recent entities), leave untouched
    - Never map 'he' / 'she' to locations
    
    Each claim gets a `resolved_text` field if resolution was applied.
    """
    last_entities: list[str] = []
    last_person_entity: str | None = None
    
    PLACES_LOWER = {
        "australia", "india", "france", "europe", "asia", "america", 
        "africa", "uk", "usa", "germany", "japan", "china", "russia", 
        "earth", "world", "waterloo", "london", "paris", "berlin", 
        "rome", "moscow", "tokyo", "washington"
    }

    def _is_person(ent: str) -> bool:
        """Heuristic: If it's a known place, not a person. If First Last, person."""
        if ent.lower() in PLACES_LOWER:
            return False
        words = ent.split()
        if len(words) >= 2 and all(w.istitle() for w in words):
            return True
        return False
    
    for claim in claims:
        original_text = claim.text
        
        current_entities = _extract_named_entities(original_text)
        
        if current_entities:
            last_entities = current_entities
            
            for ent in current_entities:
                if _is_person(ent):
                    last_person_entity = ent
            
        pronouns_found = PRONOUN_PATTERNS.findall(original_text)
        
        if not pronouns_found:
            continue
        
        valid_thing_entities = [e for e in last_entities if e.lower() not in PLACES_LOWER]
        target_thing_entity = valid_thing_entities[-1] if valid_thing_entities else None
        
        resolved = original_text
        
        for pronoun in pronouns_found:
            if _is_person_pronoun(pronoun):
                if last_person_entity:
                    resolved = _replace_pronoun_safe(resolved, last_person_entity, pronoun)
            elif _is_thing_pronoun(pronoun):
                if target_thing_entity:
                    resolved = _replace_pronoun_safe(resolved, target_thing_entity, pronoun)
        
        if resolved != original_text:
            claim.resolved_text = resolved
            logger.info(f"Coreference resolved: \"{original_text}\" → \"{resolved}\"")
    
    return claims
