from pydantic import BaseModel, Field

class AnalysisRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=10,
        max_length=8000,
        description="The text to be analyzed for claims."
    )

    class Config:
        extra = "forbid"
        str_strip_whitespace = True