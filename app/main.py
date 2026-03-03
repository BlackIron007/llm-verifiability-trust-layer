from urllib import request
from fastapi import FastAPI
from app.schemas.analysis_request import AnalysisRequest
from app.schemas.analysis_response import AnalysisResponse
from app.modules.claim_extractor import extract_claims
from app.modules.claim_classifier import classify_claim
from app.modules.risk_scorer import assign_baseline_risk, compute_overall_trust_score
from app.modules.verifiability_engine import refine_verifiability

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

    claims = extract_claims(request.text)
    classified_claims = [classify_claim(c) for c in claims]
    scored_claims = [assign_baseline_risk(c) for c in classified_claims]
    refined_claims = [refine_verifiability(c) for c in scored_claims]
    overall_score = compute_overall_trust_score(refined_claims)

    return AnalysisResponse(
        original_text=request.text,
        claims=refined_claims,
        overall_trust_score=overall_score,
        message="Full pipeline completed with verifiability refinement."
    )