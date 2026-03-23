"use client";

import { useState } from "react";
import { explainClaim } from "../lib/api";

export default function ClaimCard({ claim, onMouseEnter, onMouseLeave }) {
  const [open, setOpen] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);
  const [explanationData, setExplanationData] = useState(null);

  let riskColor = "text-textSecondary";
  let confidenceLabel = "Unknown";
  
  if (claim.risk_level === "low") {
    riskColor = "text-green-600";
    confidenceLabel = "High Confidence";
  } else if (claim.risk_level === "medium") {
    riskColor = "text-amber-500";
    confidenceLabel = "Medium Confidence";
  } else if (claim.risk_level === "high") {
    riskColor = "text-red-500";
    confidenceLabel = "Low Confidence";
  }

  const handleToggle = async () => {
    const newState = !open;
    setOpen(newState);
    
    if (newState && !explanationData) {
      setIsExplaining(true);
      try {
        const data = await explainClaim(claim.text);
        setExplanationData(data);
      } finally {
        setIsExplaining(false);
      }
    }
  };

  return (
    <div 
      className="border border-border rounded-lg p-6 bg-background shadow-sm hover:shadow-md hover:scale-[1.01] transition-all duration-300"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <div className="flex justify-between items-start gap-4">
        <p className="text-base text-text leading-relaxed font-light">{claim.text}</p>
        <div className={`text-right ${riskColor}`}>
          <div className="text-sm font-medium whitespace-nowrap">{confidenceLabel}</div>
          <div className="text-xs font-light opacity-80 mt-0.5">{(claim.verifiability_score * 100).toFixed(0)}% Score</div>
        </div>
      </div>

      <div className="mt-3 text-sm text-textSecondary font-light leading-relaxed">
        {claim.confidence_explanation?.[0]}
      </div>

      <button
        onClick={handleToggle}
        className="mt-4 text-sm text-accent hover:text-primary transition-colors duration-200 focus:outline-none"
      >
        {open ? "Hide Details" : "View Reasoning"}
      </button>

      {open && (
        <div className="mt-5 pt-5 border-t border-border transition-all duration-300">
          {/* Score Breakdown Bars */}
          <div className="space-y-4">
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-textSecondary">
                <span>Evidence Support</span>
                <span>{((claim.score_breakdown?.support ?? 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-surface rounded-full h-1.5 overflow-hidden border border-border">
                <div className="bg-text h-full rounded-full transition-all duration-500" style={{ width: `${(claim.score_breakdown?.support ?? 0) * 100}%` }}></div>
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-textSecondary">
                <span>QA Alignment</span>
                <span>{((claim.score_breakdown?.qa_alignment ?? 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-surface rounded-full h-1.5 overflow-hidden border border-border">
                <div className="bg-text h-full rounded-full transition-all duration-500" style={{ width: `${(claim.score_breakdown?.qa_alignment ?? 0) * 100}%` }}></div>
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-textSecondary">
                <span>Contradiction</span>
                <span>{((claim.score_breakdown?.contradictions ?? 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-surface rounded-full h-1.5 overflow-hidden border border-border">
                <div className="bg-text h-full rounded-full transition-all duration-500" style={{ width: `${(claim.score_breakdown?.contradictions ?? 0) * 100}%` }}></div>
              </div>
            </div>
          </div>

          {/* Evidence Panel */}
          {claim.evidence?.length > 0 && (
            <div className="mt-6 space-y-4">
              <h4 className="text-xs uppercase tracking-wider text-textSecondary font-medium">Sources</h4>
              {claim.evidence.map((ev, idx) => (
                <div key={idx} className="flex gap-3 text-sm">
                  <img src={`https://www.google.com/s2/favicons?domain=${ev.domain || ''}&sz=32`} className="w-4 h-4 mt-0.5 rounded-sm opacity-80" alt="" />
                  <div>
                    <div className="font-medium text-text">{ev.domain || ev.source}</div>
                    <div className="text-textSecondary font-light leading-relaxed mt-1">"{ev.evidence}"</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Dynamic Explanation Section */}
          <div className="mt-6 p-4 bg-surface rounded text-sm text-textSecondary font-light leading-relaxed border border-border">
            {isExplaining ? (
              <div className="animate-pulse space-y-2">
                <div className="h-2 bg-border rounded w-full"></div>
                <div className="h-2 bg-border rounded w-5/6"></div>
                <div className="h-2 bg-border rounded w-4/6"></div>
              </div>
            ) : explanationData ? (
              <div className="space-y-3">
                {explanationData.error_category && (
                  <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-red-50 text-red-600 text-xs font-medium border border-red-100">
                    ⚠️ {explanationData.error_category}
                  </span>
                )}
                <p className="text-text">{explanationData.explanation}</p>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}