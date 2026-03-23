export async function verify(text) {
  const res = await fetch("http://localhost:8000/api/v1/verify_llm_response", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question: text,
      answer: text,
    }),
  });

  return res.json();
}

export async function explainClaim(claimText) {
  const res = await fetch("http://localhost:8000/api/v1/explain", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      claim_text: claimText,
    }),
  });

  return res.json();
}