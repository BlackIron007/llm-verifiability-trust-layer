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
    num_evidence = len(evidence_list)

    CONFIDENCE_THRESHOLD = 0.6

    for ev in evidence_list:

        support_score = ev.support_score or 0.0
        label = ev.support_label or "neutral"

        if support_score < CONFIDENCE_THRESHOLD:
            label = "neutral"

        score = support_score * (ev.source_trust or 0.5)

        if label == "supports":
            support_total += score
        elif label == "contradicts":
            contradiction_total += score
        elif label == "neutral" and (ev.similarity or 0) > 0.7:
            support_total += (ev.similarity or 0) * (ev.source_trust or 0.5) * 0.3

    support_strength = support_total / num_evidence if num_evidence > 0 else 0.0
    contradiction_strength = contradiction_total / num_evidence if num_evidence > 0 else 0.0

    return {
        "support_strength": round(support_strength, 3),
        "contradiction_strength": round(contradiction_strength, 3)
    }