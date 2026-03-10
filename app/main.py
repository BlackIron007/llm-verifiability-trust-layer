from fastapi import FastAPI
from app.schemas.analysis_request import AnalysisRequest
from app.schemas.analysis_response import AnalysisResponse
from app.modules.claim_extractor import extract_claims
from app.modules.claim_classifier import classify_claim
from app.modules.risk_scorer import assign_baseline_risk, compute_overall_trust_score
from app.modules.verifiability_engine import refine_verifiability
from app.schemas.llm_request import LLMVerificationRequest
from app.services.relevance_service import compute_qa_relevance
from app.services.evidence_service import retrieve_evidence
from app.modules.consistency_checker import check_question_claim_consistency
from app.schemas.claim import RiskLevel

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
        signals={
            "epistemic_risk": 1 - overall_score
        },
        message="Full pipeline completed with verifiability refinement."
    )
    
@app.post("/verify_llm_response", response_model=AnalysisResponse)
def verify_llm_response(request: LLMVerificationRequest):

    question = request.question
    answer = request.answer
    
    claims = extract_claims(answer)
    classified_claims = [classify_claim(c) for c in claims]
    scored_claims = [assign_baseline_risk(c) for c in classified_claims]
    refined_claims = [refine_verifiability(c) for c in scored_claims]

    relevance_score = compute_qa_relevance(question, answer)

    for claim in refined_claims:
        try:
            claim.evidence = retrieve_evidence(claim.text)
        except Exception as e:
            print("Evidence retrieval error:", e)
            claim.evidence = []
        
        contradictions = [
            ev for ev in claim.evidence
            if ev.support_label == "contradicts" and ev.support_score > 0.7
        ]

        if contradictions:
            claim.verifiability_score = 1.0
            claim.risk_level = RiskLevel.HIGH

        is_consistent, sim = check_question_claim_consistency(question, claim.text)
        claim.qa_consistent = is_consistent
        claim.qa_similarity = round(sim, 3)

        if not is_consistent:
            claim.verifiability_score = 1.0
            claim.risk_level = RiskLevel.HIGH
    
    epistemic_trust = compute_overall_trust_score(refined_claims)
    epistemic_risk = 1 - epistemic_trust

    final_trust_score = round(relevance_score * epistemic_trust, 3)
    
    signals = {
        "qa_relevance": relevance_score,
        "epistemic_risk": round(epistemic_risk, 3),
        "epistemic_trust": round(epistemic_trust, 3)
    }

    return AnalysisResponse(
        original_text=answer,
        claims=refined_claims,
        overall_trust_score=final_trust_score,
        signals=signals,
        message="LLM response verification completed."
    )