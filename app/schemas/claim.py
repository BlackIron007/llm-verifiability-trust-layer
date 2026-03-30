from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from enum import Enum
from typing import List
from app.schemas.evidence import Evidence


class ClaimType(str, Enum):
    HARD_FACT = "hard_fact"
    SOFT_FACT = "soft_fact"
    OPINION = "opinion"
    PREDICTION = "prediction"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class VerificationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNVERIFIABLE = "UNVERIFIABLE"
    CONTRADICTED = "CONTRADICTED"

class Claim(BaseModel):
    id: Optional[int] = None
    text: str
    original_index: Optional[int] = None
    claim_type: Optional[ClaimType] = None
    verifiability_score: Optional[float] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    risk_level: Optional[RiskLevel] = None
    verification_status: Optional[VerificationStatus] = None
    explanation: Optional[str] = None
    secondary_explanation: Optional[str] = None
    tertiary_explanation: Optional[str] = None
    evidence: List[Evidence] = []
    qa_consistent: bool | None = None
    qa_similarity: float | None = None
    support_strength: float | None = None
    contradiction_strength: float | None = None
    confidence_explanation: list[str] | None = None
    resolved_text: Optional[str] = None
    score_breakdown: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True