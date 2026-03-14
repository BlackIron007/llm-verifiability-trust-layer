from pydantic import BaseModel
from typing import List
from app.schemas.llm_request import LLMVerificationRequest

class BatchVerificationRequest(BaseModel):
    items: List[LLMVerificationRequest]