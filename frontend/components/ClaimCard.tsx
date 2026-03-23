"use client";

import { useState } from "react";

export default function ClaimCard({ claim, onMouseEnter, onMouseLeave }) {
  const [open, setOpen] = useState(false);

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
        onClick={() => setOpen(!open)}
        className="mt-4 text-sm text-accent hover:text-primary transition-colors duration-200 focus:outline-none"
      >
        {open ? "Hide Details" : "View Reasoning"}
      </button>

      {open && (
        <div className="mt-5 pt-5 border-t border-border text-sm space-y-3 font-light text-textSecondary">
          <div className="flex justify-between items-center">
            <span>Evidence Support</span>
            <span className="text-text">{claim.score_breakdown?.support ?? 0}</span>
          </div>
          <div className="flex justify-between items-center">
            <span>QA Alignment</span>
            <span className="text-text">{claim.score_breakdown?.qa_alignment ?? 0}</span>
          </div>
        </div>
      )}
    </div>
  );
}