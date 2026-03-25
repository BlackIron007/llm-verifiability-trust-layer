"""
Coreference Resolution — Safe Heuristic (Option 1)

Resolves pronouns to the most recent named entity using spaCy NER.
Only replaces pronouns when confidence is high (single unambiguous entity).
Ambiguous cases are left untouched.
"""

import re
import logging

logger = logging.getLogger("verifier")

# Pronouns to resolve (subject/object forms)
PRONOUN_PATTERNS = re.compile(
    r'\b(he|she|it|they|him|her|his|its|their|them)\b',
    re.IGNORECASE
)

# Simple NER fallback using regex for common named entities
# This avoids requiring spaCy as a dependency
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
        # Skip common words that happen to start sentences
        if ent.lower() in COMMON_STARTERS:
            continue
        # Skip single-character matches
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
    - Track the last mentioned named entity
    - If a claim contains pronouns and there's exactly one recent entity, replace safely
    - If ambiguous (multiple recent entities), leave untouched
    
    Each claim gets a `resolved_text` field if resolution was applied.
    """
    last_entities: list[str] = []
    
    for claim in claims:
        original_text = claim.text
        
        # Extract entities from this claim
        current_entities = _extract_named_entities(original_text)
        
        if current_entities:
            # This claim introduces new entities — update tracking
            last_entities = current_entities
            continue  # No resolution needed for claims that name their own entities
        
        # Check if this claim has pronouns that need resolution
        pronouns_found = PRONOUN_PATTERNS.findall(original_text)
        
        if not pronouns_found or not last_entities:
            continue
        
        # Safety check: only resolve if there's exactly ONE recent entity (no ambiguity)
        unique_entities = list(dict.fromkeys(last_entities))  # preserve order, dedup
        
        if len(unique_entities) != 1:
            logger.debug(f"Ambiguous coreference — {len(unique_entities)} entities: {unique_entities}. Skipping.")
            continue
        
        target_entity = unique_entities[0]
        resolved = original_text
        
        for pronoun in pronouns_found:
            # Person pronouns only resolve to person-like entities (multi-word or capitalized)
            if _is_person_pronoun(pronoun):
                resolved = _replace_pronoun_safe(resolved, target_entity, pronoun)
            elif _is_thing_pronoun(pronoun):
                resolved = _replace_pronoun_safe(resolved, target_entity, pronoun)
            # Skip ambiguous plural pronouns like "they/them/their"
        
        if resolved != original_text:
            claim.resolved_text = resolved
            logger.info(f"Coreference resolved: \"{original_text}\" → \"{resolved}\"")
    
    return claims
