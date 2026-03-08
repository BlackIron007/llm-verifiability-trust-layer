import wikipedia
from app.services.embedding_service import compute_similarity
from app.schemas.evidence import Evidence
import nltk
from nltk.tokenize import sent_tokenize


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

                evidence_list.append(
                    Evidence(
                        source="Wikipedia",
                        title=title,
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