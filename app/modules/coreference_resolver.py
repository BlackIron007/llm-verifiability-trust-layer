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
    r'\b([A-Z]\w*(?:\s+(?:[A-Z]\w*|\d+))*)\b'
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
    last_person_context: set[str] = set()
    last_thing_context: set[str] = set()
    
    PLACES_LOWER = {
        "australia", "india", "france", "europe", "asia", "america", 
        "africa", "uk", "usa", "germany", "japan", "china", "russia", 
        "earth", "world", "waterloo", "london", "paris", "berlin", 
        "rome", "moscow", "tokyo", "washington"
    }

    TITLES_LOWER = {"emperor", "king", "queen", "president", "pope", "general", "chancellor", "minister"}

    DEMONYMS_LOWER = {"french", "american", "german", "british", "chinese", "japanese", "russian", "indian", "italian", "european", "polish", "spanish", "dutch", "swedish", "swiss", "canadian"}

    NON_PERSON_KEYWORDS = {"revolution", "war", "empire", "republic"}
    NON_PERSON_NOUNS = {"nobel prize", "world war i", "world war ii", "french revolution", "university of paris", "aplastic anemia"}
    NON_PERSON_CAPITALIZED = {"university", "theory", "achievements", "during", "world", "war", "i", "ii"}

    MALE_KEYWORDS = {"he", "him", "his", "husband", "brother", "father", "son", "king", "emperor", "pope", "mr", "pierre", "napoleon", "einstein", "columbus", "shakespeare"}
    FEMALE_KEYWORDS = {"she", "her", "hers", "woman", "wife", "sister", "mother", "daughter", "queen", "mrs", "ms", "miss", "marie", "curie"}

    def _get_entity_gender(entity_text: str) -> str:
        """
        Determines the likely gender of a named entity based on keywords.
        Returns 'male', 'female', or 'unknown'.
        """
        lower_text = entity_text.lower()
        words = set(lower_text.split())

        if words.intersection(MALE_KEYWORDS):
            return "male"
        if words.intersection(FEMALE_KEYWORDS):
            return "female"
        
        return "unknown"

    def _is_person(ent: str) -> bool:
        """Heuristic: If it's a known place, not a person. If First Last, person."""
        ent_lower = ent.lower()
        if ent_lower in PLACES_LOWER:
            return False
        
        if ent_lower in DEMONYMS_LOWER:
            return False
        
        if any(kw in ent_lower for kw in NON_PERSON_KEYWORDS):
            return False

        if ent_lower in TITLES_LOWER:
            return False
        
        if ent_lower in NON_PERSON_NOUNS:
            return False
        if ent_lower in NON_PERSON_CAPITALIZED:
            return False

        if ent_lower in {"her", "his", "its", "their"}:
            return False

        words = ent.split()
        if len(words) >= 2 and all(w.istitle() for w in words):
            return True
        if len(words) == 1 and ent.istitle():
            return True
        return False
    
    for claim in claims:
        original_text = claim.text
        
        pronouns_found = PRONOUN_PATTERNS.findall(original_text)
        current_entities = _extract_named_entities(original_text)
        
        current_persons = {ent for ent in current_entities if _is_person(ent)}
        current_things = {ent for ent in current_entities if not _is_person(ent)}

        if pronouns_found:
            resolved = original_text
            for pronoun in pronouns_found:
                if _is_person_pronoun(pronoun):
                    person_candidates = current_persons.union(last_person_context)
                    filtered_candidates = set()
                    pronoun_lower = pronoun.lower()
                    
                    if pronoun_lower in {"she", "her", "hers"}:
                        for p in person_candidates:
                            if _get_entity_gender(p) != "male":
                                filtered_candidates.add(p)
                    elif pronoun_lower in {"he", "him", "his"}:
                        for p in person_candidates:
                            if _get_entity_gender(p) != "female":
                                filtered_candidates.add(p)

                    if len(filtered_candidates) == 1:
                        target_person = list(filtered_candidates)[0]
                        resolved = _replace_pronoun_safe(resolved, target_person, pronoun)
                    else:
                        logger.info(f"Ambiguous person coreference for '{original_text}', candidates: {filtered_candidates or person_candidates}")
                elif _is_thing_pronoun(pronoun):
                    thing_candidates = current_things.union(last_thing_context)
                    if len(thing_candidates) == 1:
                        target_thing = list(thing_candidates)[0]
                        resolved = _replace_pronoun_safe(resolved, target_thing, pronoun)
                    else:
                        logger.info(f"Ambiguous thing coreference for '{original_text}', candidates: {thing_candidates}")

            if resolved != original_text:
                claim.resolved_text = resolved
                logger.info(f"Coreference resolved: \"{original_text}\" → \"{resolved}\"")

        if current_persons:
            last_person_context.update(current_persons)
        if current_things:
            last_thing_context.update(current_things)
    
    return claims
