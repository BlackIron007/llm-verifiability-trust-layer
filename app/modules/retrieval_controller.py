def evidence_is_weak(evidence_list):
    """
    Determine if retrieved evidence is weak.
    """

    if not evidence_list:
        return True

    top_score = max((e.evidence_score or 0) for e in evidence_list)

    if top_score < 0.6:
        return True

    return False


def refine_query(claim_text):
    """
    Generate a refined search query.
    """

    return f"{claim_text} fact history explanation"