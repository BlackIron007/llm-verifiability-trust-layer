from app.services.embedding_service import compute_similarity
from app.schemas.evidence import Evidence
import nltk
from nltk.tokenize import sent_tokenize
import httpx
from urllib.parse import quote
from app.services.global_cache import embedding_cache

def best_sentence_match(claim_text: str, paragraph: str):
    """
    Find the sentence in a paragraph that best matches the claim,
    and return a 3-sentence context window (prev, best, next) to aid NLI comprehension.
    """
    try:
        sentences = sent_tokenize(paragraph) if paragraph else []
    except Exception:
        sentences = [paragraph] if paragraph else []

    best_score = 0.0
    best_idx = -1

    for i, sentence in enumerate(sentences):
        try:
            cache_key = hash(frozenset({claim_text, sentence}))
            if cache_key not in embedding_cache:
                embedding_cache[cache_key] = compute_similarity(claim_text, sentence)
            score = embedding_cache[cache_key]
        except Exception:
            score = 0.0
        if score > best_score:
            best_score = score
            best_idx = i

    if best_idx == -1:
        return "", 0.0

    start_idx = max(0, best_idx - 1)
    end_idx = min(len(sentences), best_idx + 2)
    best_sentence_window = " ".join(sentences[start_idx:end_idx])

    return best_sentence_window, best_score


from ddgs import DDGS
from app.services.source_trust_service import compute_source_trust, get_trust_level_label, extract_domain
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger("verifier")

def retrieve_evidence(claim_text: str, top_k: int = 3, mode: str = "full"):
    """
    Implements a tiered evidence retrieval strategy for performance and reliability.
    Tier 1: Wikipedia (fast, high-trust)
    Tier 2: DuckDuckGo Search (fallback, skipped in 'fast' mode)
    """
    logger.info(f"Tier 1 Retrieval: Querying Wikipedia for '{claim_text}'")
    wiki_evidence = retrieve_wikipedia_evidence(claim_text, top_k=2)

    if mode == "fast":
        logger.info("Fast mode: Skipping web search.")
        return wiki_evidence

    if wiki_evidence and any(ev.similarity > 0.8 for ev in wiki_evidence):
        logger.info("Tier 1 successful, strong evidence found. Skipping web search.")
        return wiki_evidence

    logger.info(f"Tier 2 Retrieval: Querying DDGS for '{claim_text}'")
    ddgs_evidence = retrieve_ddgs_evidence(claim_text, top_k=2)

    all_evidence = wiki_evidence + ddgs_evidence
    all_evidence.sort(
        key=lambda x: (x.similarity or 0) * 0.7 + (x.source_trust or 0) * 0.3,
        reverse=True
    )

    return all_evidence


def retrieve_wikipedia_evidence(claim_text: str, top_k: int = 3):
    """
    Retrieves evidence paragraphs from Wikipedia
    and ranks them by semantic similarity to the claim.
    """

    USER_AGENT = "VeritasAI/1.0 (https://github.com/BlackIron007/llm-verifiability-trust-layer; sdev43083@gmail.com)"
    HEADERS = {"User-Agent": USER_AGENT}
    TIMEOUT = 2.0

    evidence_list = []

    try:
        search_url = (
            "https://en.wikipedia.org/w/api.php?action=opensearch"
            f"&search={quote(claim_text)}&limit={top_k}&namespace=0&format=json"
        )
        with httpx.Client(headers=HEADERS, timeout=TIMEOUT) as client:
            search_response = client.get(search_url)
            search_response.raise_for_status()
            search_results = search_response.json()

        page_titles = search_results[1] if len(search_results) > 1 else []

        for title in page_titles:
            try:
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
                with httpx.Client(headers=HEADERS, timeout=TIMEOUT) as client:
                    summary_response = client.get(summary_url)
                    if summary_response.status_code != 200:
                        continue
                    page_data = summary_response.json()

                page_title = page_data.get("title", "")
                page_url = page_data.get("content_urls", {}).get("desktop", {}).get("page", "")
                summary = page_data.get("extract", "")

                if not all([page_title, page_url, summary]):
                    continue

                JUNK_WORD_GROUPS = [
                    ["film", "movie", "motion picture"],
                    ["album", "record"],
                    ["song", "track"],
                    ["book", "novel", "publication"],
                    ["series", "show"],
                    ["list of", "lists of"]
                ]
                
                is_irrelevant_media = False
                title_lower = page_title.lower()
                claim_lower = claim_text.lower()

                for group in JUNK_WORD_GROUPS:
                    title_has_keyword = any(keyword in title_lower for keyword in group)
                    if title_has_keyword:
                        claim_has_keyword = any(keyword in claim_lower for keyword in group)
                        if not claim_has_keyword:
                            is_irrelevant_media = True
                            break
                if is_irrelevant_media:
                    continue

                best_sentence, similarity = best_sentence_match(claim_text, summary)

                if similarity >= 0.6:
                    trust_score = compute_source_trust(page_url)
                    evidence_list.append(
                        Evidence(
                            source="Wikipedia",
                            title=page_title,
                            url=page_url,
                            evidence=best_sentence,
                            similarity=round(similarity, 3),
                            source_trust=trust_score,
                            source_trust_level=get_trust_level_label(trust_score),
                            domain="wikipedia.org"
                        )
                    )

            except (httpx.RequestError, Exception) as e:
                logger.warning(f"Failed to process Wikipedia title '{title}': {e}")
                continue
    except (httpx.RequestError, Exception) as e:
        logger.error(f"Wikipedia evidence retrieval failed: {e}")
        pass

    evidence_list.sort(key=lambda x: x.similarity, reverse=True)

    return evidence_list[:top_k]


def retrieve_ddgs_evidence(claim_text: str, top_k: int = 3):
    evidence_list = []

    BLOCKED_DOMAINS = [
        "maps.google",
        "google.ru/maps",
        "youtube.com",
        "pinterest.com"
    ]

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(claim_text, max_results=top_k))

            for r in results:
                title = r.get("title", "")
                url = r.get("href", "")
                if any(b in url for b in BLOCKED_DOMAINS):
                    continue

                snippet = r.get("body") or r.get("snippet") or ""

                if not snippet:
                    continue

                best_sentence, similarity = best_sentence_match(claim_text, snippet)

                if similarity >= 0.5:
                    trust_score = compute_source_trust(url)
                    evidence_list.append(
                        Evidence(
                            source="DDGS",
                            title=title,
                            url=url,
                            evidence=best_sentence,
                            similarity=round(similarity, 3),
                            source_trust=trust_score,
                            source_trust_level=get_trust_level_label(trust_score),
                            domain=extract_domain(url)
                        )
                    )

    except Exception as e:
        print("DDGS ERROR:", e)

    return evidence_list[:top_k]