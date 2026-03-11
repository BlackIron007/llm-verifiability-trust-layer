def aggregate_evidence(evidence_list):
    """
    Combine multiple evidence items into a single support signal.
    """

    if not evidence_list:
        return {
            "support_strength": 0.0,
            "contradiction_strength": 0.0
        }

    support_total = 0
    contradiction_total = 0

    for ev in evidence_list:

        score = (ev.support_score or 0) * (ev.source_trust or 0.5)

        if ev.support_label == "supports":
            support_total += score

        elif ev.support_label == "contradicts":
            contradiction_total += score

    total = support_total + contradiction_total

    if total == 0:
        return {
            "support_strength": 0.0,
            "contradiction_strength": 0.0
        }

    return {
        "support_strength": round(support_total / total, 3),
        "contradiction_strength": round(contradiction_total / total, 3)
    }