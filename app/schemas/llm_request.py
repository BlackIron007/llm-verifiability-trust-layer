from pydantic import BaseModel

class LLMVerificationRequest(BaseModel):
    question: str
    answer: str