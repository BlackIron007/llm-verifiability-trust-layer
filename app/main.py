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
from app.services.nli_service import check_claim_evidence_support_batch
from nltk.tokenize import sent_tokenize
from app.api_key import verify_api_key
from fastapi.responses import StreamingResponse, JSONResponse
import json
import asyncio
from app.services.evidence_cache import get_cached_evidence, set_cached_evidence
from collections import defaultdict

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
    """Handles application startup and shutdown events."""
    check_local_nltk_data()
    logger.info("Application startup: Warming up models...")
    loop = asyncio.get_event_loop()

    def run_warmup():
        warmup_queries = [
            "Key events of World War 2",
            "Scientific evidence for climate change",
            "History of the internet"
        ]
        with ThreadPoolExecutor(max_workers=len(warmup_queries)) as executor:
            list(executor.map(_fetch_evidence, warmup_queries))

    await loop.run_in_executor(None, run_warmup)
    logger.info("Application startup: Models are warm and ready.")
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

def _fetch_evidence(search_query: str) -> list:
    """
    A helper function designed to be run in a thread pool.
    It retrieves evidence for a single search query, utilizing the global cache.
    """
    cached = get_cached_evidence(search_query)
    if cached is not None:
        logger.info(f"Global cache hit for query: '{search_query}'")
        return cached
    
    logger.info(f"Cache miss for query: '{search_query}'")
    evidence = retrieve_evidence(search_query)
    evidence = summarize_evidence(evidence)
    set_cached_evidence(search_query, evidence)
    return evidence

def _finalize_claim_processing(claim, question):
    """
    Takes a claim with its evidence already attached and performs the final
    aggregation, scoring, and calibration steps. Designed to be run in parallel.
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

    agg = aggregate_evidence(claim.evidence)
    claim.support_strength = agg["support_strength"]
    claim.contradiction_strength = agg["contradiction_strength"]
    
    if claim.contradiction_strength > 0.2:
        penalty = claim.contradiction_strength * 0.5
        claim.verifiability_score = min(1.0, (claim.verifiability_score or 0) + penalty)

    is_consistent, sim = check_question_claim_consistency(question, claim.text)
    claim.qa_consistent = is_consistent
    claim.qa_similarity = round(sim, 3)

    if claim.support_strength > 0.7:
        claim.verifiability_score = max(0.05, (claim.verifiability_score or 0.3) - 0.15)
    elif claim.support_strength > 0.5:
        claim.verifiability_score = max(0.05, (claim.verifiability_score or 0.3) - 0.10)
    elif claim.support_strength > 0.3:
        claim.verifiability_score = max(0.05, (claim.verifiability_score or 0.3) - 0.05)

    claim = calibrate_claim_trust(claim)

    claim.confidence_explanation = generate_confidence_explanation(claim)

    if not is_consistent:
        claim.verifiability_score = min(1.0, (claim.verifiability_score or 0) + 0.6)
    
    claim.verifiability_score = round(claim.verifiability_score or 0, 3)
    claim.risk_level = compute_risk_level(claim.verifiability_score)
    return claim

def _core_verify(question: str, answer: str, mode: str = "full") -> AnalysisResponse:
    """Internal service function containing the core verification logic."""
    claims = extract_claims(answer)
    with ThreadPoolExecutor(max_workers=4) as executor:
        classified_claims = list(executor.map(classify_claim, claims))
        
    scored_claims = [assign_baseline_risk(c) for c in classified_claims]
    refined_claims = [refine_verifiability(c) for c in scored_claims]

    claims_to_process_fully = []
    processed_claims_early = []

    for claim in refined_claims:
        is_low_risk_fact = claim.claim_type == ClaimType.HARD_FACT and (claim.verifiability_score or 1.0) <= 0.3
        if mode == "fast" and is_low_risk_fact:
            claim.confidence_explanation = ["Low-risk factual claim. Deep verification skipped in fast mode."]
            claim.support_strength = 1.0 
            claim.contradiction_strength = 0.0
            processed_claims_early.append(claim)
        else:
            claims_to_process_fully.append(claim)

    relevance_score = compute_qa_relevance(question, answer)

    claims_by_text = defaultdict(list)
    unique_claim_texts = set()
    for claim in claims_to_process_fully:
        if claim.claim_type != ClaimType.OPINION:
            claims_by_text[claim.text].append(claim)
            unique_claim_texts.add(claim.text)

    all_unique_queries = list(unique_claim_texts)

    evidence_map = {}
    if all_unique_queries:
        with ThreadPoolExecutor(max_workers=8) as executor:
            evidence_results = list(executor.map(_fetch_evidence, all_unique_queries))
        evidence_map = dict(zip(all_unique_queries, evidence_results))

    for text, claims_group in claims_by_text.items():
        all_evidence = evidence_map.get(text, [])
        
        pruned_evidence = [ev for ev in all_evidence if (ev.similarity or 0) > 0.6]
        
        evidence_limit = 1 if mode == "fast" else 2
        final_evidence = pruned_evidence[:evidence_limit]
        for claim in claims_group:
            claim.evidence = final_evidence

    nli_cache = {} 
    nli_batch_pairs = []
    nli_batch_targets = []

    for claim in claims_to_process_fully:
        if claim.claim_type == ClaimType.OPINION:
            continue

        evidence_to_process = claim.evidence[:1]

        for ev in evidence_to_process:
            if (ev.similarity or 0) > 0.7 and (ev.source_trust or 0) >= 0.9:
                ev.support_label = "supports"
                ev.support_score = 0.95
                continue

            cache_key = (claim.text, ev.evidence)
            if cache_key in nli_cache:
                ev.support_label, ev.support_score = nli_cache[cache_key]
                continue
            
            nli_batch_pairs.append((claim.text, ev.evidence))
            nli_batch_targets.append(ev)

    if nli_batch_pairs:
        batch_results = check_claim_evidence_support_batch(nli_batch_pairs)
        for i, (label, score) in enumerate(batch_results):
            ev = nli_batch_targets[i]
            ev.support_label = label
            ev.support_score = score
            cache_key = (nli_batch_pairs[i][0], nli_batch_pairs[i][1])
            nli_cache[cache_key] = (label, score)

    for claim in claims_to_process_fully:
        for ev in claim.evidence:
            if ev.support_label is None:
                ev.support_label = "neutral"
                ev.support_score = 0.5

    with ThreadPoolExecutor(max_workers=8) as executor:
        fully_processed_claims = list(
            executor.map(lambda c: _finalize_claim_processing(c, question), claims_to_process_fully)
        )
    
    final_claims = processed_claims_early + fully_processed_claims

    epistemic_trust = compute_overall_trust_score(final_claims)

    if final_claims and all(c.claim_type == ClaimType.OPINION for c in final_claims):
        epistemic_trust *= 0.3

    contradictions = detect_internal_contradictions(final_claims)

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
        claims=final_claims,
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
    mode = payload.mode
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Verify LLM response request from IP: {client_ip} in '{mode}' mode.")
    return _core_verify(payload.question, payload.answer, mode=mode)

async def stream_verification(question: str, answer: str):
    """
    Splits an answer into sentences, verifies each sentence, and streams the results.
    """
    loop = asyncio.get_running_loop()
    sentences = sent_tokenize(answer)

    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [
            loop.run_in_executor(executor, _core_verify, question, s.strip())
            for s in sentences if s.strip()
        ]
        for future in asyncio.as_completed(tasks):
            result = await future
            yield f"data: {json.dumps(result.dict())}\n\n"

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
async def verify_batch(
    payload: BatchVerificationRequest,
    request: Request
):
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Verify batch request from IP: {client_ip} with {len(payload.items)} items")

    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [
            loop.run_in_executor(executor, _core_verify, item.question, item.answer, item.mode)
            for item in payload.items
        ]
        results = await asyncio.gather(*tasks)

    return {"results": results}

app.include_router(router)