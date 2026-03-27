import time
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:8000/api/v1/verify_llm_response"

TESTS = [
    {
        "name": "1. Multi-hop coreference",
        "question": "Tell me about Napoleon.",
        "answer": "Napoleon ruled France. He fought many wars. He lost at Waterloo. He died in 1821."
    },
    {
        "name": "2. Entity ambiguity",
        "question": "Did Apple release a product?",
        "answer": "Apple released a product. It became popular. Apple is also a fruit."
    },
    {
        "name": "3. Contradiction inside same entity",
        "question": "Is the Earth flat?",
        "answer": "The Earth is flat. The Earth is round."
    },
    {
        "name": "4. Subtle contradiction",
        "question": "At what temperature does water boil?",
        "answer": "Water boils at 100°C. Water boils at 90°C at sea level."
    },
    {
        "name": "5. Temporal reasoning",
        "question": "When did World War 2 end?",
        "answer": "World War 2 ended in 1945. It ended in 1939."
    },
    {
        "name": "6. Pronoun failure case",
        "question": "Who was smarter, Einstein or Tesla?",
        "answer": "Einstein met Tesla. He was a genius."
    },
    {
        "name": "7. Mixed truth + false",
        "question": "What did Einstein do?",
        "answer": "Einstein developed relativity. He invented the internet."
    },
    {
        "name": "8. Vague claim",
        "question": "Is technology getting better?",
        "answer": "Technology is improving rapidly."
    },
    {
        "name": "9. Numeric trap",
        "question": "What is the speed of light?",
        "answer": "The speed of light is 300,000 km/s. It is 150,000 km/s."
    },
    {
        "name": "10. Real-world tricky",
        "question": "When did India gain independence?",
        "answer": "India gained independence in 1947. It became a republic in 1950."
    }
]

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
    
    print("Starting tests in 2s...")
    time.sleep(2)
    for test in TESTS:
        print(f"Running: {test['name']}")
        start_time = time.time()
        
        try:
            resp = requests.post(API_URL, json={"question": test["question"], "answer": test["answer"], "mode": "full"}, headers=headers)
            latency = time.time() - start_time
                
            data = resp.json()
            
            results_md += f"## {test['name']}\n"
            results_md += f"**Input:** `{test['answer']}`\n"
            results_md += f"**Latency:** {latency*1000:.0f}ms\n\n"
            
            results_md += f"### System Output:\n"
            if 'overall_trust_score' in data:
                results_md += f"- **Overall Confidence:** {data['overall_trust_score']*100:.1f}%\n"
                results_md += f"- **Internally Consistent?** {'No' if data.get('contradictions') else 'Yes'}\n"
                
                results_md += "\n**Detailed Claims:**\n"
                for i, claim in enumerate(data.get("claims", [])):
                    results_md += f"{i+1}. `{claim.get('text')}`\n"
                    results_md += f"   - Resolved: *{claim.get('resolved_text') or 'N/A'}*\n"
                    results_md += f"   - Verification Status: **{claim.get('verification_status')}** (Risk Level: {claim.get('risk_level')})\n"
                    results_md += f"   - Base Info: Similarity: {claim.get('qa_similarity')}, Contradiction Strength: {claim.get('contradiction_strength')}\n"
                    
            else:
                results_md += f"Error / Unsupported response structure: {data}\n"
                
        except Exception as e:
            results_md += f"**Execution failed!** Exception: {e}\n"
            
        results_md += "---\n\n"
        
    out_path = "analysis_results.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(results_md)
    print(f"Saved results to {out_path}")

if __name__ == "__main__":
    run_tests()
