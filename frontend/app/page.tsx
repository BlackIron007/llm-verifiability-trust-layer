"use client";

import InputBar from "../components/InputBar";
import TrustSummary from "../components/TrustSummary";
import ClaimCard from "../components/ClaimCard";
import { useState } from "react";
import { verify } from "../lib/api";

export default function Page() {
  const [data, setData] = useState(null);

  const handleSubmit = async (text) => {
    const res = await verify(text);
    setData(res);
  };

  return (
    <div className="min-h-screen bg-background text-text font-sans font-light tracking-wide px-6 py-12 md:py-16">
      <div className="max-w-3xl mx-auto space-y-12">
        <InputBar onSubmit={handleSubmit} />

        {data && (
          <>
            <TrustSummary data={data} />

            <div className="border border-border rounded-lg p-8 bg-surface shadow-sm">
              <h2 className="text-xl font-light text-text mb-4">📄 Verified Answer</h2>
              <p className="text-base text-text leading-relaxed font-light whitespace-pre-wrap">
                {data.original_text}
              </p>
            </div>

            <div className="space-y-6">
              {data.claims.map((c, i) => (
                <ClaimCard key={i} claim={c} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}