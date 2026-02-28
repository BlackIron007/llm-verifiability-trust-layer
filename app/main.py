from fastapi import FastAPI
from app.schemas.analysis_request import AnalysisRequest
from app.schemas.analysis_response import AnalysisResponse

app = FastAPI(
    title="LLM Verifiability & Trust Layer",
    description="Middleware system for claim extraction and verifiability analysis",
    version="0.1.0"
)


@app.get("/")
def root():
    return {"message": "LLM Verifiability Trust Layer API is running"}


@app.post("/analyze", response_model=AnalysisResponse)
def analyze_text(request: AnalysisRequest):
    """
    Temporary placeholder.
    Real AI logic will be added later.
    """

    return AnalysisResponse(
        original_text=request.text,
        claims=[],
        overall_trust_score=0.0,
        message="Analysis pipeline initialized. Claim extraction not yet implemented."
    )