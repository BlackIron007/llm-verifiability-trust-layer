from pydantic import BaseModel, Field
from typing import Optional
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

class Claim(BaseModel):
    id: Optional[int] = None
    text: str
    claim_type: Optional[ClaimType] = None
    verifiability_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    explanation: Optional[str] = None
    secondary_explanation: Optional[str] = None
    tertiary_explanation: Optional[str] = None
    evidence: List[Evidence] = []