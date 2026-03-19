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

    CONFIDENCE_THRESHOLD = 0.6

    for ev in evidence_list:

        support_score = ev.support_score or 0.0
        # Robustness: Treat a null label as "neutral" to ensure consistent processing.
        label = ev.support_label or "neutral"

        if support_score < CONFIDENCE_THRESHOLD:
            label = "neutral"

        score = support_score * (ev.source_trust or 0.5)

        if label == "supports":
            support_total += score

        elif label == "contradicts":
            contradiction_total += score
        
        elif label == "neutral" and (ev.similarity or 0) > 0.7:
            support_total += score * 0.3

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