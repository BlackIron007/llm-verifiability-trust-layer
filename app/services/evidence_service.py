import wikipedia
from app.services.embedding_service import compute_similarity
from app.schemas.evidence import Evidence
import nltk
from nltk.tokenize import sent_tokenize

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
            score = compute_similarity(claim_text, sentence)
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

def retrieve_evidence(claim_text: str, top_k: int = 3):
    """
    Implements a tiered evidence retrieval strategy for performance and reliability.
    Tier 1: Wikipedia (fast, high-trust)
    Tier 2: DuckDuckGo Search (fallback)
    """
    logger.info(f"Tier 1 Retrieval: Querying Wikipedia for '{claim_text}'")
    wiki_evidence = retrieve_wikipedia_evidence(claim_text, top_k=2)
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

    evidence_list = []

    try:
        search_results = wikipedia.search(claim_text, results=top_k)

        for title in search_results:

            try:
                page = wikipedia.page(title)
                summary = page.summary

                JUNK_WORD_GROUPS = [
                    ["film", "movie", "motion picture"],
                    ["album", "record"],
                    ["song", "track"],
                    ["book", "novel", "publication"],
                    ["series", "show"],
                    ["list of", "lists of"]
                ]
                
                is_irrelevant_media = False
                title_lower = page.title.lower()
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
                    trust_score = compute_source_trust(page.url)
                    evidence_list.append(
                        Evidence(
                            source="Wikipedia",
                            title=page.title,
                            url=page.url,
                            evidence=best_sentence,
                            similarity=round(similarity, 3),
                            source_trust=trust_score,
                            source_trust_level=get_trust_level_label(trust_score),
                            domain="wikipedia.org"
                        )
                    )

            except Exception:
                continue

    except Exception:
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