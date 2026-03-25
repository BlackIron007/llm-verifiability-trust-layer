def generate_confidence_explanation(claim):
    """
    Generate human-readable explanation for claim trust score.
    """

    explanations = []

    if getattr(claim, "support_strength", 0) > 0.6:
        explanations.append("High model confidence — strong corroborating evidence.")

    elif getattr(claim, "support_strength", 0) > 0.3:
        explanations.append("Weak or insufficient evidence found.")

    else:
        explanations.append("No credible supporting evidence found.")

    if getattr(claim, "contradiction_strength", 0) > 0.5:
        explanations.append("Significant contradictory evidence detected.")

    elif getattr(claim, "contradiction_strength", 0) > 0.2:
        explanations.append("Some contradictory evidence detected.")

    else:
        explanations.append("No strong contradictions detected.")

    if getattr(claim, "qa_consistent", True):
        explanations.append("Claim is consistent with the question.")
    else:
        explanations.append("Claim may not directly answer the question.")

    return explanations