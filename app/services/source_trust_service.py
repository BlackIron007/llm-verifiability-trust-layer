from urllib.parse import urlparse

HIGH_TRUST_DOMAINS = [
    "wikipedia.org",
    "britannica.com",
    "who.int",
    "nature.com",
    "science.org"
]

MEDIUM_TRUST_DOMAINS = [
    "nytimes.com",
    "bbc.com",
    "reuters.com",
    "theguardian.com",
    "washingtonpost.com"
]

HIGH_TRUST_WEIGHT = 0.9
MEDIUM_TRUST_WEIGHT = 0.75
LOW_TRUST_WEIGHT = 0.5
SOCIAL_MEDIA_WEIGHT = 0.2


SOCIAL_DOMAINS = [
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com"
]

def extract_domain(url: str):

    try:
        domain = urlparse(url).netloc.lower()
        return domain.replace("www.", "")
    except Exception:
        return ""

def get_trust_level_label(score: float) -> str:
    if score >= HIGH_TRUST_WEIGHT:
        return "High Trust"
    if score >= MEDIUM_TRUST_WEIGHT:
        return "Medium Trust"
    return "Low Trust"


def compute_source_trust(url: str):

    domain = extract_domain(url)

    if any(s in domain for s in SOCIAL_DOMAINS):
        return SOCIAL_MEDIA_WEIGHT

    if any(d in domain for d in HIGH_TRUST_DOMAINS):
        return HIGH_TRUST_WEIGHT

    if domain.endswith(".gov") or domain.endswith(".edu"):
        return HIGH_TRUST_WEIGHT

    if any(d in domain for d in MEDIUM_TRUST_DOMAINS):
        return MEDIUM_TRUST_WEIGHT

    return LOW_TRUST_WEIGHT