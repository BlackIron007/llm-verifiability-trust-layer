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
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
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
from app.schemas.claim import Claim, RiskLevel, ClaimType, VerificationStatus
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
from app.services.global_cache import evidence_cache, nli_cache
from app.modules.query_rewriter import rewrite_query
from app.modules.intra_answer_checker import check_world_knowledge_contradictions
from app.modules.coreference_resolver import resolve_coreferences
from app.services.verification_store import init_db, save_verification, get_recent_verifications
from app.modules.coreference_resolver import _extract_named_entities
from collections import defaultdict
from pydantic import BaseModel
import re

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
    init_db()
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

QUALIFIER_PHRASES = {
    "at sea level", "in a vacuum", "on earth", "on mars", "at room temperature",
    "under normal conditions", "in the northern hemisphere", "in the southern hemisphere",
    "during the day", "at night"
}


def _fetch_evidence(search_query: str, mode: str = "full") -> list:
    """
    A helper function designed to be run in a thread pool.
    It retrieves evidence for a single search query, utilizing the global cache.
    """
    cache_key = hash(search_query)
    if cache_key in evidence_cache:
        logger.info(f"Global cache hit for query: '{search_query}'")
        return evidence_cache[cache_key]
    
    logger.info(f"Cache miss for query: '{search_query}'")
    evidence = retrieve_evidence(search_query, mode=mode)
    evidence = summarize_evidence(evidence)
    evidence_cache[cache_key] = evidence
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

        claim.verifiability_score = 0.3
        claim.risk_level = RiskLevel.LOW

        claim.confidence_explanation = [
            "Claim classified as opinion.",
            "Fact verification skipped.",
            "Opinions are not objectively verifiable."
        ]
        return claim

    agg = aggregate_evidence(claim.evidence)
    support = agg["support_strength"]
    contradiction = agg["contradiction_strength"]
                
    claim.support_strength = support
    claim.contradiction_strength = contradiction
    
    is_consistent, sim = check_question_claim_consistency(question, claim.resolved_text or claim.text)
    claim.qa_consistent = is_consistent
    claim.qa_similarity = round(sim, 3)

    if claim.contradiction_strength > 0.3:
        claim.verification_status = VerificationStatus.CONTRADICTED
    elif claim.support_strength >= 0.5:
        claim.verification_status = VerificationStatus.SUPPORTED
    else:
        is_factual_claim = claim.claim_type in [ClaimType.HARD_FACT, ClaimType.SOFT_FACT]
        effective_text = claim.resolved_text or claim.text
        entities = _extract_named_entities(effective_text)
        is_entity_year_pattern = len(entities) > 0 and re.search(r'\b\d{4}\b', effective_text)
        is_general_entity_fact = len(entities) > 0 and len(effective_text.split()) < 15

        if is_factual_claim and (is_entity_year_pattern or is_general_entity_fact):
            logger.info(f"Evidence fallback (weak evidence override): Marking '{claim.text}' as SUPPORTED due to high-confidence pattern.")
            claim.verification_status = VerificationStatus.SUPPORTED
            claim.support_strength = max(claim.support_strength or 0.0, 0.8)
        elif claim.support_strength < 0.4 and claim.claim_type != ClaimType.OPINION:
            claim.verification_status = VerificationStatus.UNSUPPORTED
        else:
            claim.verification_status = VerificationStatus.UNVERIFIABLE

    claim.verifiability_score = round(claim.verifiability_score or 0, 3)
    claim.risk_level = compute_risk_level(claim.verifiability_score)
    claim.confidence_explanation = generate_confidence_explanation(claim)

    claim.score_breakdown = {
        "support": claim.support_strength,
        "contradictions": claim.contradiction_strength,
        "qa_alignment": claim.qa_similarity
    }

    if hasattr(claim, "evidence") and claim.evidence:
        claim.evidence.sort(
            key=lambda x: ((x.support_score or 0) * (x.source_trust or 0.5)),
            reverse=True
        )

    return claim

def _core_verify(question: str, answer: str, mode: str = "full") -> AnalysisResponse:
    """Internal service function containing the core verification logic."""
    
    if len(answer.split()) > 10:
        speculative_query = rewrite_query(answer)
        bg_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='speculative_fetch')
        bg_executor.submit(_fetch_evidence, speculative_query, mode=mode)
        bg_executor.shutdown(wait=False)
        logger.info(f"Speculatively fetching evidence for query: '{speculative_query}'")

    claims = extract_claims(answer)
    for i, claim in enumerate(claims):
        claim.original_index = i

    claims = resolve_coreferences(claims)
    
    try:
        sentences = sent_tokenize(answer)
        sentence_offsets = []
        curr_pos = 0
        for s in sentences:
            start = answer.find(s, curr_pos)
            if start != -1:
                sentence_offsets.append((s, start, start + len(s)))
                curr_pos = start + len(s)
        
        for claim in claims:
            exact_idx = answer.lower().find(claim.text.lower())
            if exact_idx != -1:
                claim.start_char = exact_idx
                claim.end_char = exact_idx + len(claim.text)
                continue
            
            claim_tokens = set(re.findall(r'\w+', claim.text.lower()))
            best_match, best_overlap = None, 0.0
            for s_text, start, end in sentence_offsets:
                s_tokens = set(re.findall(r'\w+', s_text.lower()))
                if not s_tokens or not claim_tokens: continue
                overlap = len(claim_tokens.intersection(s_tokens)) / len(claim_tokens.union(s_tokens))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = (start, end)
            
            if best_overlap > 0.3 and best_match:
                claim.start_char = best_match[0]
                claim.end_char = best_match[1]
    except Exception as e:
        logger.warning(f"Failed to compute citation offsets: {e}")

    classified_claims = []
    if claims:
        with ThreadPoolExecutor(max_workers=min(4, len(claims))) as executor:
            classified_claims = list(executor.map(classify_claim, claims))
        
    scored_claims = [assign_baseline_risk(c) for c in classified_claims]
    refined_claims = [refine_verifiability(c) for c in scored_claims]

    detect_internal_contradictions(refined_claims, mode="rules_only")

    claims_to_process_fully = []
    processed_claims_early = []

    for claim in refined_claims:
        if claim.verification_status is not None:
            if not getattr(claim, 'confidence_explanation', None) and getattr(claim, 'explanation', None):
                claim.confidence_explanation = [claim.explanation]
            processed_claims_early.append(claim)
            continue
        
        if claim.verification_status == VerificationStatus.CONTRADICTED:
            processed_claims_early.append(claim)
            continue

        is_low_risk_hard_fact = claim.claim_type == ClaimType.HARD_FACT and (claim.verifiability_score or 1.0) <= 0.3
        is_very_simple_fact = len(claim.text.split()) < 8

        if is_low_risk_hard_fact and is_very_simple_fact:
            claim.confidence_explanation = ["Simple, low-risk factual claim. Fast-tracked verification."]
            claim.support_strength = 1.0
            claim.contradiction_strength = 0.0
            claim.verification_status = VerificationStatus.SUPPORTED
            processed_claims_early.append(claim)
            continue

        if mode == "fast" and is_low_risk_hard_fact:
            claim.confidence_explanation = ["Low-risk factual claim. Fast verification mode applied."]
            claim.support_strength = 1.0
            claim.contradiction_strength = 0.0
            claim.verification_status = VerificationStatus.SUPPORTED
            processed_claims_early.append(claim)
            continue
        
        claims_to_process_fully.append(claim)

    relevance_score = 0.9 if len(answer.split()) < 40 else compute_qa_relevance(question, answer)

    query_to_claims_map = defaultdict(list)
    query_to_risk = {}
    for claim in claims_to_process_fully:
        if claim.claim_type != ClaimType.OPINION:
            eff_text = claim.resolved_text or claim.text
            rewritten_query = rewrite_query(eff_text)
            logger.info(f"Rewrote query: '{eff_text}' -> '{rewritten_query}'")
            query_to_claims_map[rewritten_query].append(claim)
            current_risk = query_to_risk.get(rewritten_query, 0.0)
            query_to_risk[rewritten_query] = max(current_risk, claim.verifiability_score or 0.5)

    all_unique_queries = list(query_to_claims_map.keys())

    EXTERNAL_API_CALL_LIMIT = 2
    if len(all_unique_queries) > EXTERNAL_API_CALL_LIMIT:
        logger.info(f"Limiting {len(all_unique_queries)} potential API calls to {EXTERNAL_API_CALL_LIMIT} based on claim risk.")
        all_unique_queries.sort(key=lambda query: query_to_risk.get(query, 0.0), reverse=True)
        all_unique_queries = all_unique_queries[:EXTERNAL_API_CALL_LIMIT]

    evidence_map = {}
    if all_unique_queries:
        with ThreadPoolExecutor(max_workers=min(8, len(all_unique_queries))) as executor:
            future_to_query = {executor.submit(_fetch_evidence, query, mode=mode): query for query in all_unique_queries}

            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    result = future.result(timeout=7.0)
                    evidence_map[query] = result
                except TimeoutError:
                    logger.warning(f"Fetching evidence for '{query}' timed out after 7 seconds.")
                except Exception as exc:
                    logger.error(f"Fetching evidence for '{query}' generated an exception: {exc}")

        for query in all_unique_queries:
            if query not in evidence_map:
                evidence_map[query] = []

    for query, claims_group in query_to_claims_map.items():
        all_evidence = evidence_map.get(query, [])
        
        pruned_evidence = [ev for ev in all_evidence if (ev.similarity or 0) > 0.6]
        
        evidence_limit = 1 if mode == "fast" else 2
        final_evidence = pruned_evidence[:evidence_limit]
        for claim in claims_group:
            claim.evidence = final_evidence

    nli_batch_pairs = []
    nli_batch_targets = []

    for claim in claims_to_process_fully:
        if claim.claim_type == ClaimType.OPINION:
            continue

        eff_text = claim.resolved_text or claim.text
        evidence_to_process = claim.evidence[:1]

        for ev in evidence_to_process:
            if mode == "fast" and (ev.similarity or 0) > 0.8:
                logger.info(f"Fast mode: Skipping NLI for high-similarity evidence (sim: {ev.similarity}).")
                ev.support_label = "supports"
                ev.support_score = 0.90
                continue

            if (ev.similarity or 0) > 0.7 and (ev.source_trust or 0) >= 0.9:
                ev.support_label = "supports"
                ev.support_score = 0.95
                continue

            cache_key = hash((eff_text, ev.evidence))
            if cache_key in nli_cache:
                ev.support_label, ev.support_score = nli_cache[cache_key]
                continue
            
            nli_batch_pairs.append((eff_text, ev.evidence))
            nli_batch_targets.append(ev)

    if nli_batch_pairs:
        batch_results = check_claim_evidence_support_batch(nli_batch_pairs)
        for i, (label, score) in enumerate(batch_results):
            ev = nli_batch_targets[i]
            ev.support_label = label
            ev.support_score = score
            cache_key = hash((nli_batch_pairs[i][0], nli_batch_pairs[i][1]))
            nli_cache[cache_key] = (label, score)

    for claim in claims_to_process_fully:
        for ev in claim.evidence:
            if ev.support_label is None:
                ev.support_label = "neutral"
                ev.support_score = 0.5

    fully_processed_claims = []
    if claims_to_process_fully:
        with ThreadPoolExecutor(max_workers=min(8, len(claims_to_process_fully))) as executor:
            fully_processed_claims = list(executor.map(lambda c: _finalize_claim_processing(c, question), claims_to_process_fully))
    
    final_claims = processed_claims_early + fully_processed_claims
    
    final_claims.sort(key=lambda c: c.original_index if hasattr(c, 'original_index') else float('inf'))

    for claim in final_claims:
        if claim.qa_consistent is None:
            is_consistent, sim = check_question_claim_consistency(question, claim.resolved_text or claim.text)
            claim.qa_consistent = is_consistent
            claim.qa_similarity = round(sim, 3)
            
            if claim.score_breakdown is None:
                claim.score_breakdown = {
                    "support": claim.support_strength or 0.0,
                    "contradictions": claim.contradiction_strength or 0.0,
                    "qa_alignment": claim.qa_similarity or 0.0
                }

    internal_contradictions = detect_internal_contradictions(final_claims)
    final_claims = check_world_knowledge_contradictions(final_claims)

    has_any_contradiction = any(c.verification_status == VerificationStatus.CONTRADICTED for c in final_claims)
    is_internally_consistent = not has_any_contradiction

    epistemic_trust = compute_overall_trust_score(final_claims)

    opinion_pattern = r'\b(think|thoughts|opinion|perspective|stance|favorite|best|feel|recommend|should|suggest)\b'
    is_opinion_soliciting = bool(re.search(opinion_pattern, question, re.IGNORECASE))
    if final_claims and all(c.claim_type == ClaimType.OPINION for c in final_claims) and not is_opinion_soliciting:
        epistemic_trust *= 0.3

    if not is_internally_consistent:
        epistemic_trust = min(epistemic_trust, 0.5)

    epistemic_risk = 1 - epistemic_trust

    final_trust_score = round(relevance_score * epistemic_trust, 3)

    summary_bullets = []
    if epistemic_trust >= 0.8:
        summary_bullets.append("Mostly correct and highly verified")
    elif epistemic_trust >= 0.5:
        summary_bullets.append("Mixed factual accuracy")
    else:
        summary_bullets.append("Factually incorrect")

    if not is_internally_consistent:
        summary_bullets.append("Internal contradictions detected")
    else:
        summary_bullets.append("Internally consistent")

    claims_with_evidence = [c for c in final_claims if c.evidence or c.support_strength is not None]
    if claims_with_evidence:
        avg_support = sum(c.support_strength or 0 for c in claims_with_evidence) / len(claims_with_evidence)
        if avg_support >= 0.7:
            summary_bullets.append("Strong overall evidence support")
        elif avg_support >= 0.4:
            summary_bullets.append("Weak or insufficient evidence")
        else:
            summary_bullets.append("No credible source supports this claim")
    else:
        summary_bullets.append("No evidence was retrieved for any claim")

    is_safe = epistemic_trust >= 0.6 and is_internally_consistent

    def claim_sort_key(c):
        """
        Defines the sorting order for claims in the final response to improve UX.
        The tuple is sorted in reverse, so higher numbers come first.

        1. Contradictions first, then other non-supported statuses, then supported last.
        2. Highest risk first (HIGH > MEDIUM > LOW).
        3. Tie-break by contradiction strength.
        """
        status_order = {
            VerificationStatus.CONTRADICTED: 3,
            VerificationStatus.UNSUPPORTED: 2,
            VerificationStatus.UNVERIFIABLE: 2,
            VerificationStatus.SUPPORTED: 1
        }
        status_score = status_order.get(c.verification_status, 0)

        risk_order = {RiskLevel.HIGH: 2, RiskLevel.MEDIUM: 1, RiskLevel.LOW: 0}
        risk_score = risk_order.get(c.risk_level, 0)

        return (status_score, risk_score, c.contradiction_strength or 0.0)

    final_claims.sort(key=claim_sort_key, reverse=True)
    
    signals = {
        "qa_relevance": relevance_score,
        "epistemic_risk": round(epistemic_risk, 3),
        "epistemic_trust": round(epistemic_trust, 3),
        "is_internally_consistent": is_internally_consistent
    }

    return AnalysisResponse(
        original_text=answer,
        claims=final_claims,
        contradictions=internal_contradictions,
        overall_trust_score=final_trust_score,
        signals=signals,
        summary_bullets=summary_bullets,
        is_safe=is_safe,
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
    result = _core_verify(payload.question, payload.answer, mode=mode)
    save_verification(payload.answer[:500], result.overall_trust_score, mode)
    
    return result

@router.get("/recent_verifications")
@limiter.limit("30/minute")
def recent_verifications(request: Request):
    """Return the most recent verification results from SQLite."""
    return get_recent_verifications(limit=10)

async def stream_verification(question: str, answer: str):
    """
    Splits an answer into sentences, verifies each sentence, and streams the results.
    """
    loop = asyncio.get_running_loop()
    sentences = sent_tokenize(answer)

    if sentences:
        with ThreadPoolExecutor(max_workers=min(4, len(sentences))) as executor:
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

    results = []
    if payload.items:
        with ThreadPoolExecutor(max_workers=min(4, len(payload.items))) as executor:
            tasks = [
                loop.run_in_executor(executor, _core_verify, item.question, item.answer, item.mode)
                for item in payload.items
            ]
            results = await asyncio.gather(*tasks)

    return {"results": results}

class ExplainRequest(BaseModel):
    claim_text: str

@router.post("/explain", dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
def explain_claim_on_demand(
    payload: ExplainRequest,
    request: Request
):
    """
    DEPRECATED. This logic is now part of the core pipeline.
    On-Demand Explanation Layer.
    Generates an explanation for a claim's trust score asynchronously to save latency on the main verification path.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Explain claim request from IP: {client_ip}")
    
    from app.services.model_client import ModelClient
    from app.services.global_cache import llm_cache
    prompt = f"""Analyze the factual verifiability of the following claim.
    Keep the explanation concise and objective.
    If the claim is likely false, unverified, or hallucinated, classify the error into a specific category (e.g., ENTITY ERROR, FACTUAL CONTRADICTION, Number Exaggeration, Anachronism, Unsupported, Logical Fallacy). You must explicitly output 'ENTITY ERROR' if there is an entity mismatch, and 'FACTUAL CONTRADICTION' if there is a factual contradiction. If the claim is well-supported and true, set the category to null.

    Respond STRICTLY in the following JSON format without any markdown or extra text:
    {{
        "explanation": "Your concise explanation here.",
        "error_category": "Category name or null"
    }}

    Claim: '{payload.claim_text}'"""
    
    cache_key = hash(prompt)
    if cache_key in llm_cache:
        raw_response = llm_cache[cache_key]
    else:
        raw_response = ModelClient.generate(prompt).strip()
        llm_cache[cache_key] = raw_response
    
    try:
        json_str = re.sub(r'^```json\s*', '', raw_response)
        json_str = re.sub(r'^```\s*', '', json_str)
        json_str = re.sub(r'\s*```$', '', json_str)
        data = json.loads(json_str)
        return data
    except Exception as e:
        logger.error(f"Failed to parse explanation JSON: {e}. Raw: {raw_response}")
        return {"explanation": raw_response, "error_category": None}

app.include_router(router)