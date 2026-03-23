from pydantic import BaseModel
from typing import Optional

class Evidence(BaseModel):
    source: str
    title: str
    url: Optional[str]
    evidence: str
    similarity: float
    support_label: str | None = None
    support_score: float | None = None
    source_trust: float | None = None
    source_trust_level: str | None = None
    domain: str | None = None
    evidence_score: float | None = None
    evidence_summary: str | None = None