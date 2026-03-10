import wikipedia
from app.services.embedding_service import compute_similarity
from app.schemas.evidence import Evidence
import nltk
from nltk.tokenize import sent_tokenize
from ddgs import DDGS
from app.services.nli_service import check_claim_evidence_support


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


def retrieve_evidence(claim_text: str, top_k: int = 3):
    evidence_list = retrieve_wikipedia_evidence(claim_text, top_k)

    if not evidence_list or max(e.similarity for e in evidence_list) < 0.4:
        evidence_list = retrieve_ddgs_evidence(claim_text, top_k)

    for ev in evidence_list:
        label, score = check_claim_evidence_support(claim_text, ev.evidence)
        ev.support_label = label
        ev.support_score = round(score, 3)

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
                            similarity=round(similarity, 3)
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

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(claim_text, max_results=top_k))

            for r in results:
                title = r.get("title", "")
                url = r.get("href", "")

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
                            similarity=round(similarity, 3)
                        )
                    )

    except Exception as e:
        print("DDGS ERROR:", e)

    evidence_list.sort(key=lambda x: x.similarity, reverse=True)

    return evidence_list[:top_k]