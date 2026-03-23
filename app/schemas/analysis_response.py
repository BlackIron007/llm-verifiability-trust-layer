from pydantic import BaseModel
from typing import List
from app.schemas.claim import Claim


class AnalysisResponse(BaseModel):
    original_text: str
    claims: List[Claim]
    overall_trust_score: float
    message: str
    signals: dict
    summary_bullets: list[str] = []
    is_safe: bool = True
    contradictions: list | None = None