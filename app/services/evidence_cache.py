import hashlib
import copy
from cachetools import TTLCache

CACHE_MAXSIZE = 1024
CACHE_TTL = 3600

_cache = TTLCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TTL)

def _hash_key(text: str) -> str:
    """
    Generate deterministic cache key for a claim.
    """
    if not text:
        return ""
    return hashlib.sha256(str(text).lower().strip().encode()).hexdigest()

def get_cached_evidence(claim_text: str):
    """
    Retrieve cached evidence if available.
    Returns a deep copy to prevent accidental mutation of the cache.
    """
    if not claim_text:
        return None
    key = _hash_key(claim_text)
    cached_data = _cache.get(key)
    return copy.deepcopy(cached_data) if cached_data is not None else None

def set_cached_evidence(claim_text: str, evidence):
    """
    Store evidence in cache.
    Stores a deep copy to prevent external mutation from altering the cache.
    """
    if not claim_text:
        return
    key = _hash_key(claim_text)
    _cache[key] = copy.deepcopy(evidence)