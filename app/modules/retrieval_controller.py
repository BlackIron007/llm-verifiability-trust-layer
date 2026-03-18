def evidence_is_weak(evidence_list):
    """
    Determine if retrieved evidence is weak.
    """

    if not evidence_list:
        return True

    top_score = max(
        (e.similarity or 0) * 0.7 + (e.source_trust or 0) * 0.3
        for e in evidence_list
    )

    if top_score < 0.55:
        return True

    return False


def refine_query(claim_text):
    """
    Generate a refined search query.
    """

    return f"{claim_text} fact history explanation"