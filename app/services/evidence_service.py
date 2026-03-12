import wikipedia
from app.services.embedding_service import compute_similarity
from app.schemas.evidence import Evidence
import nltk
from nltk.tokenize import sent_tokenize
from ddgs import DDGS
from app.services.nli_service import check_claim_evidence_support
from app.services.source_trust_service import compute_source_trust
from app.modules.retrieval_controller import evidence_is_weak, refine_query


def compute_evidence_score(similarity, support_score, source_trust):
    """
    Compute a final ranking score for evidence.
    """

    similarity = similarity or 0
    support_score = support_score or 0
    source_trust = source_trust or 0

    score = (
        0.4 * similarity +
        0.4 * support_score +
        0.2 * source_trust
    )

    return round(score, 3)


def best_sentence_match(claim_text: str, paragraph: str):
    """
    Find the sentence in a paragraph that best matches the claim.
    """
    try:
        sentences = sent_tokenize(paragraph) if paragraph else []
    except Exception:
        sentences = [paragraph] if paragraph else []

    best_sentence = ""
    best_score = 0.0

    for sentence in sentences:
        try:
            score = compute_similarity(claim_text, sentence)
        except Exception:
            score = 0.0
        if score > best_score:
            best_score = score
            best_sentence = sentence

    return best_sentence, best_score


def _score_evidence_list(claim_text: str, evidence_list: list[Evidence]):
    """Scores a list of evidence items against a claim."""
    for ev in evidence_list:
        label, score = check_claim_evidence_support(claim_text, ev.evidence)
        ev.support_label = label
        ev.support_score = round(score, 3)
        ev.evidence_score = compute_evidence_score(
            ev.similarity,
            ev.support_score,
            ev.source_trust
        )
    return evidence_list


def retrieve_evidence(claim_text: str, top_k: int = 3):
    evidence_list = retrieve_wikipedia_evidence(claim_text, top_k)
    evidence_list = _score_evidence_list(claim_text, evidence_list)

    if evidence_is_weak(evidence_list):
        print("Iterative retrieval triggered")
        refined_query = refine_query(claim_text)
        ddgs_evidence = retrieve_ddgs_evidence(refined_query, top_k)

        if ddgs_evidence:
            evidence_list = _score_evidence_list(claim_text, ddgs_evidence)

    evidence_list.sort(
        key=lambda x: x.evidence_score if x.evidence_score else 0,
        reverse=True
    )

    return evidence_list


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

                best_sentence, similarity = best_sentence_match(claim_text, summary)

                if similarity >= 0.4:
                    evidence_list.append(
                        Evidence(
                            source="Wikipedia",
                            title=page.title,
                            url=page.url,
                            evidence=best_sentence,
                            similarity=round(similarity, 3),
                            source_trust=compute_source_trust(page.url)
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

                if similarity >= 0.30:
                    evidence_list.append(
                        Evidence(
                            source="DDGS",
                            title=title,
                            url=url,
                            evidence=best_sentence,
                            similarity=round(similarity, 3),
                            source_trust=compute_source_trust(url)
                        )
                    )

    except Exception as e:
        print("DDGS ERROR:", e)

    return evidence_list[:top_k]