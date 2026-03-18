import hashlib
import copy
from cachetools import TTLCache
from app.schemas.claim import ClaimType

CACHE_MAXSIZE = 2048
CACHE_TTL = 86400     

_cache: TTLCache = TTLCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TTL)

def _hash_key(text: str) -> str:
    """
    Generate a deterministic cache key for a claim text.
    """
    if not text:
        return ""
    return hashlib.sha256(str(text).lower().strip().encode()).hexdigest()

def get_cached_classification(claim_text: str) -> ClaimType | None:
    """
    Retrieve a cached claim classification if available.
    """
    if not claim_text:
        return None
    key = _hash_key(claim_text)
    return _cache.get(key)

def set_cached_classification(claim_text: str, claim_type: ClaimType):
    """
    Store a claim classification in the cache.
    """
    if not claim_text:
        return
    key = _hash_key(claim_text)
    _cache[key] = claim_type