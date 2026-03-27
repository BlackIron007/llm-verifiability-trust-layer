def is_high_confidence_evidence(ev):
    """Checks if evidence is a high-confidence hit based on similarity and source trust."""
    return (ev.similarity or 0) > 0.7 and (ev.source_trust or 0) >= 0.9

def is_high_confidence_contradiction(ev):
    """Checks if evidence is a high-confidence contradiction."""
    return ev.support_label == "contradicts" and (ev.support_score or 0) > 0.8 and (ev.source_trust or 0) >= 0.75

def aggregate_evidence(evidence_list):
    """
    Combine multiple evidence items into a single support signal.
    """

    if not evidence_list:
        return {
            "support_strength": 0.0,
            "contradiction_strength": 0.0
        }

    if any(is_high_confidence_evidence(ev) for ev in evidence_list):
        return {
            "support_strength": 1.0,
            "contradiction_strength": 0.0
        }

    if any(is_high_confidence_contradiction(ev) for ev in evidence_list):
        return {
            "support_strength": 0.0,
            "contradiction_strength": 1.0
        }

    support_total = 0
    contradiction_total = 0
    num_evidence = len(evidence_list)

    CONFIDENCE_THRESHOLD = 0.6

    for ev in evidence_list:

        support_score = ev.support_score or 0.0
        label = ev.support_label or "neutral"

        if (ev.similarity or 0) < 0.5 and label == "supports":
            label = "neutral"

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