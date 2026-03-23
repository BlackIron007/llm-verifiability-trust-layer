"use client";

import InputBar from "../components/InputBar";
import TrustSummary from "../components/TrustSummary";
import ClaimCard from "../components/ClaimCard";
import { useState } from "react";
import { verify } from "../lib/api";

export default function Page() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hoveredClaimIndex, setHoveredClaimIndex] = useState<number | null>(null);
  const [showUnsafeOverride, setShowUnsafeOverride] = useState(false);

  const handleSubmit = async (text, mode) => {
    setIsLoading(true);
    setData(null);
    setShowUnsafeOverride(false);
    try {
      const res = await verify(text, mode);
      setData(res);
    } finally {
      setIsLoading(false);
    }
  };

  const renderOriginalText = () => {
    if (!data) return null;
    if (hoveredClaimIndex === null || !data.claims[hoveredClaimIndex]) {
      return data.original_text;
    }

    const claim = data.claims[hoveredClaimIndex];
    if (claim.start_char == null || claim.end_char == null) return data.original_text;

    const before = data.original_text.substring(0, claim.start_char);
    const highlight = data.original_text.substring(claim.start_char, claim.end_char);
    const after = data.original_text.substring(claim.end_char);

    return (
      <>
        {before}
        <mark className="bg-border text-text px-1 rounded transition-colors duration-300">{highlight}</mark>
        {after}
      </>
    );
  };

  return (
    <div className="min-h-screen bg-background text-text font-sans font-light tracking-wide px-6 py-12 md:py-16">
      <div className="max-w-3xl mx-auto space-y-12">
        <InputBar onSubmit={handleSubmit} isLoading={isLoading} />

        {isLoading && (
          <div className="space-y-6 animate-pulse">
            <div className="h-32 bg-surface border border-border rounded-lg shadow-sm"></div>
            <div className="h-32 bg-surface border border-border rounded-lg shadow-sm"></div>
            <div className="space-y-4">
              <div className="h-24 bg-background border border-border rounded-lg shadow-sm"></div>
              <div className="h-24 bg-background border border-border rounded-lg shadow-sm"></div>
            </div>
          </div>
        )}

        {data && (
          !data.is_safe && !showUnsafeOverride ? (
            <div className="border border-red-200 bg-red-50 rounded-lg p-10 text-center space-y-5 shadow-sm animate-fadeIn">
              <div className="text-4xl">⚠️</div>
              <div>
                <h2 className="text-xl text-red-800 font-medium mb-1">This response may be unreliable</h2>
                <p className="text-sm text-red-600/80 font-light">High epistemic risk or internal contradictions detected.</p>
              </div>
              <button 
                onClick={() => setShowUnsafeOverride(true)} 
                className="mt-4 text-sm border border-red-200 bg-white text-red-700 px-6 py-2 rounded hover:bg-red-50 transition-colors duration-200 shadow-sm"
              >
                View anyway
              </button>
            </div>
          ) : (
            <div className="space-y-12 animate-fadeIn">
              <TrustSummary data={data} />
  
              <div className="border border-border rounded-lg p-8 bg-surface shadow-sm transition-all duration-300">
                <h2 className="text-xl font-light text-text mb-4">📄 Verified Answer</h2>
                <p className="text-base text-text leading-relaxed font-light whitespace-pre-wrap">
                  {renderOriginalText()}
                </p>
              </div>
  
              <div className="space-y-6">
                {data.claims.map((c, i) => (
                  <div key={i} className="opacity-0 animate-fadeIn" style={{ animationDelay: `${i * 100}ms` }}>
                    <ClaimCard 
                      claim={c} 
                      onMouseEnter={() => setHoveredClaimIndex(i)}
                      onMouseLeave={() => setHoveredClaimIndex(null)}
                    />
                  </div>
                ))}
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
}