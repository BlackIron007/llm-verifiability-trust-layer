"use client";

import { useState } from "react";

const faqs = [
  {
    q: "What does the trust score mean?",
    a: "The trust score represents how well-supported an AI response is by real-world evidence. A higher score means the claims are backed by reliable sources, while a lower score indicates unverified or contradicted statements.",
  },
  {
    q: "How is evidence collected?",
    a: "TrustLayer searches across multiple knowledge sources in real time, retrieves relevant passages, and uses natural language inference to determine whether each source supports or contradicts the AI's claims.",
  },
  {
    q: "What is the difference between Quick Scan and Deep Analysis?",
    a: "Quick Scan performs a surface-level check — it skips deep evidence gathering for low-risk factual claims to return results faster. Deep Analysis runs the full verification pipeline including evidence retrieval, NLI scoring, and cross-reference checks for every claim.",
  },
  {
    q: "Can I use this for any AI model?",
    a: "Yes. TrustLayer is model-agnostic. Paste the AI's response regardless of which model generated it — GPT, Claude, Gemini, Llama, or any other. The verification pipeline works on the content itself.",
  },
  {
    q: "What claim types are detected?",
    a: "The system classifies claims into four types: Hard Facts (objectively verifiable), Soft Facts (contextually verifiable), Opinions (subjective), and Predictions (forward-looking). Each type is scored differently based on its verifiability.",
  },
];

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section id="faq" className="max-w-3xl mx-auto">
      <h2 className="text-3xl font-light text-primary tracking-tight mb-12 text-center">
        Questions
      </h2>

      <div className="border-t border-border">
        {faqs.map((faq, i) => (
          <div key={i} className="border-b border-border">
            <button
              onClick={() => setOpenIndex(openIndex === i ? null : i)}
              className="w-full flex items-center justify-between py-6 text-left group"
            >
              <span className="text-base font-normal text-primary pr-8">
                {faq.q}
              </span>
              <span
                className={`text-textSecondary text-xl transition-transform duration-300 ${
                  openIndex === i ? "rotate-45" : ""
                }`}
              >
                +
              </span>
            </button>
            <div
              className={`overflow-hidden transition-all duration-300 ${
                openIndex === i ? "max-h-48 pb-6" : "max-h-0"
              }`}
            >
              <p className="text-sm text-textSecondary font-light leading-relaxed pr-12">
                {faq.a}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
