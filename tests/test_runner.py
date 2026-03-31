import time
import sys
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:8000/api/v1/verify_llm_response"

TESTS = [
    {
        "name": "1. Multi-hop coreference",
        "question": "Who was Napoleon?",
        "answer": "Napoleon Bonaparte was a French military leader. He rose to prominence during the French Revolution. He was Emperor of the French from 1804 until 1814.",
        "expected": {
            "min_confidence": 0.8,
            "should_detect_contradiction": False,
            "must_be_supported": ["Napoleon Bonaparte was a French military leader."]
        }
    },
    {
        "name": "2. Entity ambiguity",
        "question": "Did Apple release a product?",
        "answer": "Apple released a new phone. It is very popular.",
        "expected": {
            "min_confidence": 0.4,
            "should_detect_contradiction": False,
        }
    },
    {
        "name": "3. Contradiction inside same entity",
        "question": "Is the Earth flat?",
        "answer": "The Earth is flat. The Earth is round.",
        "expected": {
            "max_confidence": 0.5,
            "should_detect_contradiction": True,
            "must_be_contradicted": ["The Earth is flat.", "The Earth is round."]
        }
    },
    {
        "name": "4. Subtle contradiction",
        "question": "At what temperature does water boil?",
        "answer": "Water boils at 100°C. Water boils at 90°C at sea level.",
        "expected": {
            "max_confidence": 0.5,
            "should_detect_contradiction": True,
            "must_be_contradicted": ["Water boils at 100°C.", "Water boils at 90°C at sea level."]
        }
    },
    {
        "name": "5. Temporal reasoning",
        "question": "When did World War 2 end?",
        "answer": "World War 2 ended in 1945. It ended in 1939.",
        "expected": {
            "max_confidence": 0.5,
            "should_detect_contradiction": True,
        }
    },
    {
        "name": "6. Pronoun failure case",
        "question": "Who was smarter, Einstein or Tesla?",
        "answer": "Einstein met Tesla. He was a genius.",
        "expected": {
            "min_confidence": 0.1,
            "should_detect_contradiction": False,
            "must_not_be_resolved": "He was a genius."
        }
    },
    {
        "name": "7. Mixed truth + false",
        "question": "What did Einstein do?",
        "answer": "Einstein developed relativity. He invented the internet.",
        "expected": {
            "max_confidence": 0.7,
            "should_detect_contradiction": False,
            "must_be_supported": ["Einstein developed relativity."],
            "must_be_contradicted": ["He invented the internet."]
        }
    },
    {
        "name": "8. Vague claim",
        "question": "Is technology getting better?",
        "answer": "Technology is improving rapidly.",
        "expected": {
            "min_confidence": 0.4,
            "must_be_unverifiable": ["Technology is improving rapidly."]
        }
    },
    {
        "name": "9. Numeric trap",
        "question": "What is the speed of light?",
        "answer": "The speed of light is 300,000 km/s. It is 150,000 km/s.",
        "expected": {
            "max_confidence": 0.5,
            "should_detect_contradiction": True,
        }
    },
    {
        "name": "10. Real-world tricky",
        "question": "When did India gain independence?",
        "answer": "India gained independence in 1947. It became a republic in 1950.",
        "expected": {
            "min_confidence": 0.8,
            "should_detect_contradiction": False,
            "must_be_supported": ["India gained independence in 1947.", "It became a republic in 1950."]
        }
    }
]

def validate_test(test_case, output):
    """Validates the output against the expected results in the test case."""
    failures = []
    expected = test_case.get("expected", {})
    claims_by_text = {c.get('text'): c for c in output.get('claims', [])}

    if "max_confidence" in expected and output.get("overall_trust_score", 1.0) > expected["max_confidence"]:
        failures.append(f"Confidence {output['overall_trust_score']} exceeded max of {expected['max_confidence']}")
    if "min_confidence" in expected and output.get("overall_trust_score", 0.0) < expected["min_confidence"]:
        failures.append(f"Confidence {output['overall_trust_score']} was below min of {expected['min_confidence']}")
    if expected.get("should_detect_contradiction") and not output.get("contradictions"):
        failures.append("Failed to detect contradiction.")
    if expected.get("should_detect_contradiction") is False and output.get("contradictions"):
        failures.append("Incorrectly detected a contradiction.")
    
    for claim_text in expected.get("must_be_contradicted", []):
        if claims_by_text.get(claim_text, {}).get("verification_status") != "CONTRADICTED":
            failures.append(f"Claim '{claim_text}' was not marked as CONTRADICTED.")
    for claim_text in expected.get("must_be_supported", []):
        if claims_by_text.get(claim_text, {}).get("verification_status") != "SUPPORTED":
            failures.append(f"Claim '{claim_text}' was not marked as SUPPORTED.")
    for claim_text in expected.get("must_be_unverifiable", []):
        if claims_by_text.get(claim_text, {}).get("verification_status") != "UNVERIFIABLE":
            failures.append(f"Claim '{claim_text}' was not marked as UNVERIFIABLE.")
    if "must_not_be_resolved" in expected:
        claim_text = expected["must_not_be_resolved"]
        if claims_by_text.get(claim_text, {}).get("resolved_text"):
            failures.append(f"Claim '{claim_text}' was incorrectly resolved.")

    return failures

def run_tests():
    api_key = os.getenv("VERIFIER_API_KEY")
    if not api_key:
        print("Error: VERIFIER_API_KEY not found in environment.")
        print("Please ensure your .env file is in the project root and contains the API key.")
        return

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    results_md = "# Stress Test Execution Results\n\n"
    all_failures = {}
    
    print("Starting tests in 2s...")
    time.sleep(2)
    for test in TESTS:
        print(f"Running: {test['name']}...", end=" ")
        start_time = time.time()
        
        try:
            #resp = requests.post(API_URL, json={"question": test["question"], "answer": test["answer"], "mode": "full"}, headers=headers)
            resp = requests.post(API_URL, json={"question": test["question"], "answer": test["answer"], "mode": "fast"}, headers=headers)
            latency = time.time() - start_time
                
            data = resp.json()
            
            failures = validate_test(test, data)
            if failures:
                print("FAILED")
                all_failures[test['name']] = failures
            else:
                print("PASSED")

            results_md += f"## {test['name']}\n"
            results_md += f"**Input:** `{test['answer']}`\n"
            results_md += f"**Latency:** {latency*1000:.0f}ms\n\n"
            
            results_md += f"### System Output:\n"
            if 'overall_trust_score' in data:
                results_md += f"- **Overall Confidence:** {data['overall_trust_score']*100:.1f}% "
                if failures:
                    results_md += f"**(FAIL)**\n"
                    for f in failures:
                        results_md += f"  - *Failure: {f}*\n"
                else:
                    results_md += f"**(PASS)**\n"

                results_md += f"- **Internally Consistent?** {'No' if data.get('contradictions') else 'Yes'}\n"
                
                results_md += "\n**Detailed Claims:**\n"
                for i, claim in enumerate(data.get("claims", [])):
                    results_md += f"{i+1}. `{claim.get('text')}`\n"
                    if claim.get('resolved_text'):
                        results_md += f"   - Resolved: *{claim.get('resolved_text')}*\n"
                    results_md += f"   - Verification Status: **{claim.get('verification_status')}** (Risk Level: {claim.get('risk_level')})\n"
                    
            else:
                results_md += f"Error / Unsupported response structure: {data}\n"
                
        except Exception as e:
            print(f"CRASHED: {e}")
            results_md += f"**Execution failed!** Exception: {e}\n"
            
        results_md += "---\n\n"
        
    out_path = "analysis_results.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(results_md)
    print(f"Saved results to {out_path}")

    if all_failures:
        print("\n--- TEST SUMMARY: SOME TESTS FAILED ---")
        for name, failures in all_failures.items():
            print(f"\n- {name}:")
            for f in failures:
                print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n--- TEST SUMMARY: ALL TESTS PASSED ---")

if __name__ == "__main__":
    run_tests()
