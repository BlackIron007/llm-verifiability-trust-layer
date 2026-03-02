from urllib import request
from fastapi import FastAPI
from app.schemas.analysis_request import AnalysisRequest
from app.schemas.analysis_response import AnalysisResponse
from app.modules.claim_extractor import extract_claims
from app.modules.claim_classifier import classify_claim

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

    cclaims = extract_claims(request.text)
    classified_claims = [classify_claim(c) for c in cclaims]

    return AnalysisResponse(
        original_text=request.text,
        claims=classified_claims,
        overall_trust_score=0.0,
        message="Claim extraction and classification completed. Scoring pending."
    )