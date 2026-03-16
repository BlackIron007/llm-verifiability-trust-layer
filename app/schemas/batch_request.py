from pydantic import BaseModel, Field
from typing import List
from app.schemas.llm_request import LLMVerificationRequest

class BatchVerificationRequest(BaseModel):
    items: List[LLMVerificationRequest] = Field(
        ...,
        max_items=50,
        description="A list of question-answer pairs to verify in a batch."
    )

    class Config:
        extra = "forbid"