"use client";

import { useState } from "react";
import { explainClaim } from "../lib/api";

interface Evidence {
  source?: string;
  domain?: string;
  evidence?: string;
  url?: string;
  support_label?: string;
  support_score?: number;
  similarity?: number;
  source_trust?: number;
}

interface ScoreBreakdown {
  support?: number;
  qa_alignment?: number;
  contradictions?: number;
}

interface ClaimData {
  text: string;
  claim_type?: string;
  risk_level?: string;
  verifiability_score?: number;
  confidence_explanation?: string[];
  score_breakdown?: ScoreBreakdown;
  evidence?: Evidence[];
  qa_consistent?: boolean;
}

interface ClaimCardProps {
  claim: ClaimData;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

const CLAIM_TYPE_LABELS: Record<string, { label: string; style: string }> = {
  hard_fact: { label: "Hard Fact", style: "border-primary/30 text-primary" },
  soft_fact: { label: "Soft Fact", style: "border-accent/40 text-accent" },
  opinion: { label: "Opinion", style: "border-textSecondary/30 text-textSecondary" },
  prediction: { label: "Prediction", style: "border-trust-medium/40 text-trust-medium" },
};

const RISK_LABELS: Record<string, { label: string; color: string }> = {
  low: { label: "Well Supported", color: "text-trust-high" },
  medium: { label: "Partially Verified", color: "text-trust-medium" },
  high: { label: "Unverified", color: "text-trust-low" },
};

export default function ClaimCard({ claim, onMouseEnter, onMouseLeave }: ClaimCardProps) {
  const [open, setOpen] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);
  const [explanationData, setExplanationData] = useState<{
    explanation?: string;
    error_category?: string | null;
  } | null>(null);

  const riskInfo = RISK_LABELS[claim.risk_level || ""] || { label: "Unknown", color: "text-textSecondary" };
  const typeInfo = CLAIM_TYPE_LABELS[claim.claim_type || ""];

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
      className="border border-border rounded-lg p-6 bg-background shadow-sm hover:shadow-md hover:scale-[1.005] transition-all duration-300"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {typeInfo && (
            <span className={`inline-block text-[10px] uppercase tracking-wider border px-2 py-0.5 rounded mb-2 ${typeInfo.style}`}>
              {typeInfo.label}
            </span>
          )}
          <p className="text-base text-text leading-relaxed font-light">{claim.text}</p>
        </div>
        <div className={`text-right flex-shrink-0 ${riskInfo.color}`}>
          <div className="text-sm font-medium whitespace-nowrap">{riskInfo.label}</div>
          <div className="text-xs font-light opacity-70 mt-0.5">
            {((claim.verifiability_score ?? 0) * 100).toFixed(0)}% risk
          </div>
        </div>
      </div>

      {/* First explanation line */}
      {claim.confidence_explanation?.[0] && (
        <div className="mt-3 text-sm text-textSecondary font-light leading-relaxed">
          {claim.confidence_explanation[0]}
        </div>
      )}

      {/* Toggle button */}
      <button
        onClick={handleToggle}
        className="mt-4 text-sm text-accent hover:text-primary transition-colors duration-200 focus:outline-none"
      >
        {open ? "Hide Details" : "View Reasoning"}
      </button>

      {/* Expanded details */}
      {open && (
        <div className="mt-5 pt-5 border-t border-border animate-fadeIn">
          {/* Score breakdown with user-friendly labels */}
          <div className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-textSecondary">
                <span>Source Verification</span>
                <span>{((claim.score_breakdown?.support ?? 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-surface rounded-full h-1.5 overflow-hidden border border-border">
                <div
                  className="bg-trust-high h-full rounded-full transition-all duration-500"
                  style={{ width: `${(claim.score_breakdown?.support ?? 0) * 100}%` }}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-textSecondary">
                <span>Answer Relevance</span>
                <span>{((claim.score_breakdown?.qa_alignment ?? 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-surface rounded-full h-1.5 overflow-hidden border border-border">
                <div
                  className="bg-accent h-full rounded-full transition-all duration-500"
                  style={{ width: `${(claim.score_breakdown?.qa_alignment ?? 0) * 100}%` }}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-textSecondary">
                <span>Conflicting Sources</span>
                <span>{((claim.score_breakdown?.contradictions ?? 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-surface rounded-full h-1.5 overflow-hidden border border-border">
                <div
                  className="bg-trust-low h-full rounded-full transition-all duration-500"
                  style={{ width: `${(claim.score_breakdown?.contradictions ?? 0) * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Evidence sources */}
          {claim.evidence && claim.evidence.length > 0 && (
            <div className="mt-6 space-y-4">
              <h4 className="text-xs uppercase tracking-wider text-textSecondary font-medium">
                Sources
              </h4>
              {claim.evidence.map((ev, idx) => (
                <div key={idx} className="flex gap-3 text-sm">
                  <img
                    src={`https://www.google.com/s2/favicons?domain=${ev.domain || ""}&sz=32`}
                    className="w-4 h-4 mt-0.5 rounded-sm opacity-80"
                    alt=""
                  />
                  <div className="min-w-0">
                    <div className="font-medium text-text">
                      {ev.url ? (
                        <a
                          href={ev.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:text-accent transition-colors"
                        >
                          {ev.domain || ev.source}
                        </a>
                      ) : (
                        ev.domain || ev.source
                      )}
                    </div>
                    <div className="text-textSecondary font-light leading-relaxed mt-1 break-words">
                      &ldquo;{ev.evidence}&rdquo;
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* AI explanation */}
          <div className="mt-6 p-4 bg-surface rounded text-sm text-textSecondary font-light leading-relaxed border border-border">
            {isExplaining ? (
              <div className="animate-pulse space-y-2">
                <div className="h-2 bg-border rounded w-full" />
                <div className="h-2 bg-border rounded w-5/6" />
                <div className="h-2 bg-border rounded w-4/6" />
              </div>
            ) : explanationData ? (
              <div className="space-y-3">
                {explanationData.error_category && (
                  <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-trust-low/10 text-trust-low text-xs font-medium border border-trust-low/20">
                    △ {explanationData.error_category}
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