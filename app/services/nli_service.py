from transformers import pipeline
import logging

nli_pipeline = pipeline(
    "text-classification",
    model="facebook/bart-large-mnli"
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