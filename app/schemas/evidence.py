from pydantic import BaseModel
from typing import Optional

class Evidence(BaseModel):
    source: str
    title: str
    url: Optional[str]
    evidence: str
    similarity: float