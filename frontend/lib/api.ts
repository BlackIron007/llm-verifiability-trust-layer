export async function verify(question: string, answer: string, mode: string = "full") {
  const res = await fetch("/api/v1/verify_llm_response", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "",
    },
    body: JSON.stringify({
      question: question.trim() || answer,
      answer: answer,
      mode: mode,
    }),
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`API Error: ${res.status} ${res.statusText} — ${errorBody}`);
  }

  return res.json();
}

export async function explainClaim(claimText: string) {
  const res = await fetch("/api/v1/explain", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "",
    },
    body: JSON.stringify({
      claim_text: claimText,
    }),
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`API Error: ${res.status} ${res.statusText} — ${errorBody}`);
  }

  return res.json();
}