import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

import logging
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("verifier")

from transformers.utils import logging as hf_logging
hf_logging.set_verbosity_error()

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, APIRouter, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
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
from app.schemas.claim import RiskLevel, ClaimType
from app.modules.intra_answer_checker import detect_internal_contradictions
from app.modules.evidence_aggregator import aggregate_evidence
from app.modules.trust_calibrator import calibrate_claim_trust
from app.modules.evidence_summarizer import summarize_evidence
from app.modules.confidence_explainer import generate_confidence_explanation
from app.schemas.batch_request import BatchVerificationRequest
from nltk.tokenize import sent_tokenize
from app.api_key import verify_api_key
from fastapi.responses import StreamingResponse, JSONResponse
import json
import asyncio
from app.services.evidence_cache import get_cached_evidence, set_cached_evidence

class LimitUploadSize(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        max_size = 1_000_000 
        if "content-length" in request.headers:
            try:
                content_length = int(request.headers["content-length"])
            except ValueError:
                content_length = max_size + 1 
            if content_length > max_size:
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request payload too large (exceeds 1MB limit)"}
                )
        return await call_next(request)

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

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(LimitUploadSize)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom exception handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={"error": f"Rate limit exceeded: {exc.detail}"},
    )

router = APIRouter(
    prefix="/api/v1",
)

@app.get("/")
@limiter.limit("30/minute")
def root(request: Request):
    return {"message": "LLM Verifiability Trust Layer API is running"}

@router.post("/analyze", response_model=AnalysisResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("15/minute")
def analyze_text(
    payload: AnalysisRequest,
    request: Request
):
    """
    Extracts, classifies, and scores claims from a given text.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Analyze request from IP: {client_ip}")

    claims = extract_claims(payload.text)
    classified_claims = [classify_claim(c) for c in claims]
    scored_claims = [assign_baseline_risk(c) for c in classified_claims]
    refined_claims = [refine_verifiability(c) for c in scored_claims]
    overall_score = compute_overall_trust_score(refined_claims)

    return AnalysisResponse(
        original_text=payload.text,
        claims=refined_claims,
        overall_trust_score=overall_score,
        signals={
            "epistemic_risk": 1 - overall_score
        },
        message="Full pipeline completed with verifiability refinement."
    )

def _process_claim(claim, question):
    """
    Process a single claim: evidence retrieval, aggregation,
    trust calibration, and scoring. This function is designed to be run in parallel.
    """
    if claim.claim_type == ClaimType.OPINION:
        claim.evidence = []
        claim.support_strength = 0
        claim.contradiction_strength = 0
        claim.qa_consistent = True
        claim.qa_similarity = 1.0

        claim.verifiability_score = 0.1
        claim.risk_level = RiskLevel.LOW

        claim.confidence_explanation = [
            "Claim classified as opinion.",
            "Fact verification skipped.",
            "Opinions are not objectively verifiable."
        ]
        return claim

    try:
        cached = get_cached_evidence(claim.text)

        if cached is not None:
            logger.info(f"Cache hit for claim: {claim.text}")
            claim.evidence = cached
        else:
            logger.info(f"Cache miss for claim: {claim.text}")
            claim.evidence = retrieve_evidence(claim.text)
            claim.evidence = summarize_evidence(claim.evidence)
            set_cached_evidence(claim.text, claim.evidence)
    except Exception as e:
        logger.error(f"Evidence retrieval error: {e}")
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
    return claim

def _core_verify(question: str, answer: str) -> AnalysisResponse:
    """Internal service function containing the core verification logic."""
    claims = extract_claims(answer)
    classified_claims = [classify_claim(c) for c in claims]
    scored_claims = [assign_baseline_risk(c) for c in classified_claims]
    refined_claims = [refine_verifiability(c) for c in scored_claims]

    relevance_score = compute_qa_relevance(question, answer)

    with ThreadPoolExecutor(max_workers=5) as executor:
        processed_claims = list(
            executor.map(lambda c: _process_claim(c, question), refined_claims)
        )
    refined_claims = processed_claims

    epistemic_trust = compute_overall_trust_score(refined_claims)

    if refined_claims and all(c.claim_type == ClaimType.OPINION for c in refined_claims):
        epistemic_trust *= 0.3

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

@router.post("/verify_llm_response", response_model=AnalysisResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
def verify_llm_response(
    payload: LLMVerificationRequest,
    request: Request
):
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Verify LLM response request from IP: {client_ip}")
    return _core_verify(payload.question, payload.answer)

async def stream_verification(question: str, answer: str):
    """
    Splits an answer into sentences, verifies each sentence, and streams the results.
    """
    sentences = sent_tokenize(answer)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        result = _core_verify(question, sentence)

        yield f"data: {json.dumps(result.dict())}\n\n"
        await asyncio.sleep(0.1)

@router.post("/verify_stream", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
async def verify_stream(
    payload: LLMVerificationRequest,
    request: Request
):
    """
    Accepts a question and an answer, and streams the verification results
    for each sentence in the answer.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Verify stream request from IP: {client_ip}")
    generator = stream_verification(payload.question, payload.answer)
    return StreamingResponse(
        generator,
        media_type="text/event-stream"
    )

@router.post("/verify_batch", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
def verify_batch(
    payload: BatchVerificationRequest,
    request: Request
):
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Verify batch request from IP: {client_ip} with {len(payload.items)} items")

    results = []

    for item in payload.items:
        result = _core_verify(item.question, item.answer)
        results.append(result)

    return {"results": results}

app.include_router(router)