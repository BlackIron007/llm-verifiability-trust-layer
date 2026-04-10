from app.services.embedding_service import compute_similarity, model
from sentence_transformers.util import cos_sim
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

    if not sentences:
        return "", 0.0

    try:
        claim_emb = model.encode(claim_text)
        sentences_emb = model.encode(sentences)
        
        scores = cos_sim(claim_emb, sentences_emb)[0]
        best_idx = scores.argmax().item()
        best_score = float(scores[best_idx])
    except Exception as e:
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

import asyncio

async def retrieve_evidence(claim_text: str, top_k: int = 3, mode: str = "full"):
    """
    Implements a tiered evidence retrieval strategy for performance and reliability.
    """
    logger.info(f"Tier 1 Retrieval: Querying Wikipedia for '{claim_text}'")

    if mode == "fast":
        logger.info("Fast mode: Skipping web search.")
        return await retrieve_wikipedia_evidence(claim_text, top_k=2)

    logger.info(f"Tier 2 Retrieval: Querying DDGS alongside Wikipedia for '{claim_text}'")

    wiki_task = asyncio.create_task(retrieve_wikipedia_evidence(claim_text, top_k=2))
    ddgs_task = asyncio.create_task(asyncio.to_thread(retrieve_ddgs_evidence, claim_text, top_k=2))

    results = await asyncio.gather(wiki_task, ddgs_task, return_exceptions=True)
    
    wiki_evidence = results[0] if not isinstance(results[0], Exception) else []
    ddgs_evidence = results[1] if not isinstance(results[1], Exception) else []

    if wiki_evidence and any((ev.similarity or 0) > 0.8 for ev in wiki_evidence):
        logger.info("Strong Wikipedia evidence found. Utilizing both sources.")

    all_evidence = wiki_evidence + ddgs_evidence
    all_evidence.sort(
        key=lambda x: (x.similarity or 0) * 0.7 + (x.source_trust or 0) * 0.3,
        reverse=True
    )

    return all_evidence


async def retrieve_wikipedia_evidence(claim_text: str, top_k: int = 3):
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
        async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
            search_response = await client.get(search_url)
            search_response.raise_for_status()
            search_results = search_response.json()

            page_titles = search_results[1] if len(search_results) > 1 else []

            async def fetch_summary(title):
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
                try:
                    summary_response = await client.get(summary_url)
                    if summary_response.status_code == 200:
                        return summary_response.json()
                except Exception as e:
                    logger.warning(f"Failed to process Wikipedia title '{title}': {e}")
                return None
            
            tasks = [fetch_summary(t) for t in page_titles]
            summaries = await asyncio.gather(*tasks)

            for page_data in summaries:
                if not page_data: continue

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

    except Exception as e:
        logger.error(f"Wikipedia evidence retrieval failed: {e}")

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