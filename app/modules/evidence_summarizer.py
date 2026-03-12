import re
from nltk.tokenize import sent_tokenize

def clean_text(text: str):
    """
    Clean messy search snippets.
    """

    if not text:
        return ""

    text = re.sub(r'\s+', ' ', text)

    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

    text = re.sub(r'([.,])([A-Za-z])', r'\1 \2', text)

    text = re.sub(r'[^A-Za-z0-9.,:;()\-\'" ]+', ' ', text)

    return text.strip()


def summarize_evidence(evidence_list, max_len=160):
    """
    Generate clean evidence summaries.
    """

    for ev in evidence_list:

        text = clean_text(ev.evidence or "")

        try:
            sentences = sent_tokenize(text)
        except Exception:
            sentences = []

        summary = ""

        for s in sentences:
            if len(summary) + len(s) <= max_len:
                summary += s + " "
            else:
                break

        summary = summary.strip()

        if not summary:
            summary = text[:max_len].rstrip() + "..."

        ev.evidence_summary = summary

    return evidence_list