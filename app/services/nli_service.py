from transformers import pipeline
import logging

nli_pipeline = pipeline(
    "text-classification",
    model="typeform/distilbert-base-uncased-mnli"
)

LABEL_MAP = {
    "ENTAILMENT": "supports",
    "CONTRADICTION": "contradicts",
    "NEUTRAL": "neutral"
}

def check_claim_evidence_support(claim: str, evidence: str):

    if not claim or not evidence:
        return "neutral", 0.0

    try:
        input_text = evidence + " </s></s> " + claim

        result = nli_pipeline(input_text)[0]

        model_label = result["label"].upper()
        score = result["score"]

        final_label = LABEL_MAP.get(model_label, "neutral")

        return final_label, score

    except Exception as e:
        logging.error(f"NLI pipeline failed: {e}")
        return "neutral", 0.0

def check_claim_evidence_support_batch(pairs: list[tuple[str, str]]):
    """
    Runs NLI inference on a batch of (claim, evidence) pairs.
    """
    if not pairs:
        return []

    try:
        inputs = [evidence + " </s></s> " + claim for claim, evidence in pairs]
        results = nli_pipeline(inputs)

        outputs = []
        for res in results:
            model_label = res["label"].upper()
            score = res["score"]
            final_label = LABEL_MAP.get(model_label, "neutral")
            outputs.append((final_label, score))
        return outputs

    except Exception as e:
        logging.error(f"NLI batch pipeline failed: {e}")
        return [("neutral", 0.0) for _ in pairs]