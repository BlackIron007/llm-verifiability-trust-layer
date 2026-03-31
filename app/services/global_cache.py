from cachetools import TTLCache
import logging

logger = logging.getLogger("verifier")

evidence_cache = TTLCache(maxsize=500, ttl=21600)

nli_cache = TTLCache(maxsize=2000, ttl=21600)

embedding_cache = TTLCache(maxsize=5000, ttl=86400)

claim_classification_cache = TTLCache(maxsize=2000, ttl=86400)

llm_cache = TTLCache(maxsize=500, ttl=7200)

logger.info("Global caches (Evidence, NLI, Embedding, Classification, LLM) initialized with TTLs.")