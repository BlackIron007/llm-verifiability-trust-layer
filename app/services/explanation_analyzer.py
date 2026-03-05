import re

def information_density(text: str) -> float:
    """
    Estimate explanation specificity using lexical diversity.
    """

    words = re.findall(r'\b\w+\b', text.lower())

    if not words:
        return 0

    unique_words = set(words)

    density = len(unique_words) / len(words)

    return density