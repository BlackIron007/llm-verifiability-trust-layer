from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    text: str = Field(..., min_length=10)