from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


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
    id: Optional[int] = Field(default=None)
    text: str = Field(..., min_length=5)
    claim_type: Optional[ClaimType] = None
    verifiability_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    risk_level: Optional[RiskLevel] = None
    explanation: Optional[str] = None