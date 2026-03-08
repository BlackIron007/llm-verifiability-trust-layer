import wikipedia
from app.services.embedding_service import compute_similarity
from app.schemas.evidence import Evidence

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

                similarity = compute_similarity(claim_text, summary)

                evidence_list.append(
                    Evidence(
                        source="Wikipedia",
                        title=title,
                        url=page.url,
                        evidence=summary,
                        similarity=round(similarity, 3)
                    )
                )

            except Exception:
                continue

    except Exception:
        pass

    evidence_list.sort(key=lambda x: x.similarity, reverse=True)

    return evidence_list[:top_k]