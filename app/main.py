import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import logging
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

from transformers.utils import logging as hf_logging
hf_logging.set_verbosity_error()

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.startup import check_local_nltk_data
from app.schemas.analysis_request import AnalysisRequest
from app.schemas.analysis_response import AnalysisResponse
from app.modules.claim_extractor import extract_claims
from app.modules.claim_classifier import classify_claim
from app.modules.risk_scorer import assign_baseline_risk, compute_overall_trust_score, compute_risk_level
from app.modules.verifiability_engine import refine_verifiability
from app.schemas.llm_request import LLMVerificationRequest
from app.services.relevance_service import compute_qa_relevance
from app.services.evidence_service import retrieve_evidence
from app.modules.consistency_checker import check_question_claim_consistency
from app.schemas.claim import RiskLevel
from app.modules.intra_answer_checker import detect_internal_contradictions
from app.modules.evidence_aggregator import aggregate_evidence
from app.modules.trust_calibrator import calibrate_claim_trust
from app.modules.evidence_summarizer import summarize_evidence
from app.modules.confidence_explainer import generate_confidence_explanation
from app.schemas.batch_request import BatchVerificationRequest
from nltk.tokenize import sent_tokenize
from fastapi.responses import StreamingResponse
import json
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    check_local_nltk_data()
    yield

app = FastAPI(
    title="LLM Verifiability & Trust Layer",
    description="Middleware system for claim extraction and verifiability analysis",
    version="0.1.0",
    lifespan=lifespan
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
            claim.evidence = summarize_evidence(claim.evidence)
        except Exception as e:
            print("Evidence retrieval error:", e)
            claim.evidence = []

        agg = aggregate_evidence(claim.evidence)
        claim.support_strength = agg["support_strength"]
        claim.contradiction_strength = agg["contradiction_strength"]
        
        if claim.contradiction_strength > 0.2:
            penalty = claim.contradiction_strength * 0.5
            claim.verifiability_score = min(1.0, (claim.verifiability_score or 0) + penalty)

        is_consistent, sim = check_question_claim_consistency(question, claim.text)
        claim.qa_consistent = is_consistent
        claim.qa_similarity = round(sim, 3)

        claim = calibrate_claim_trust(claim)

        claim.confidence_explanation = generate_confidence_explanation(claim)

        if not is_consistent:
            claim.verifiability_score = min(1.0, (claim.verifiability_score or 0) + 0.6)
        
        claim.risk_level = compute_risk_level(claim.verifiability_score)
    
    epistemic_trust = compute_overall_trust_score(refined_claims)
    contradictions = detect_internal_contradictions(refined_claims)

    if contradictions:
        epistemic_trust *= 0.5

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
        contradictions=contradictions,
        overall_trust_score=final_trust_score,
        signals=signals,
        message="LLM response verification completed."
    )

async def stream_verification(question: str, answer: str):
    """
    Splits an answer into sentences, verifies each sentence, and streams the results.
    """
    sentences = sent_tokenize(answer)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        request = LLMVerificationRequest(
            question=question,
            answer=sentence
        )

        result = verify_llm_response(request)

        yield f"data: {json.dumps(result.dict())}\n\n"
        await asyncio.sleep(0.1)

@app.post("/verify_stream")
async def verify_stream(request: LLMVerificationRequest):
    """
    Accepts a question and an answer, and streams the verification results
    for each sentence in the answer.
    """
    generator = stream_verification(request.question, request.answer)
    return StreamingResponse(
        generator,
        media_type="text/event-stream"
    )

@app.post("/verify_batch")
def verify_batch(request: BatchVerificationRequest):

    results = []

    for item in request.items:

        single_request = LLMVerificationRequest(
            question=item.question,
            answer=item.answer
        )

        result = verify_llm_response(single_request)

        results.append(result)

    return {"results": results}