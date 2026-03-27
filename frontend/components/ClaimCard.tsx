"use client";

import { useState } from "react";
import { explainClaim } from "../lib/api";
import { Database, AlignLeft, TrendingUp, MessageSquare, AlertCircle } from "lucide-react";

interface Evidence {
  source?: string;
  domain?: string;
  evidence?: string;
  url?: string;
}

interface ScoreBreakdown {
  support?: number;
  qa_alignment?: number;
  contradictions?: number;
}

interface ClaimData {
  text: string;
  resolved_text?: string;
  claim_type?: string;
  risk_level?: string;
  verifiability_score?: number;
  verification_status?: string;
  support_strength?: number;
  contradiction_strength?: number;
  confidence_explanation?: string[];
  score_breakdown?: ScoreBreakdown;
  evidence?: Evidence[];
}

interface ClaimCardProps {
  claim: ClaimData;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

const TYPE_SYMBOLS: Record<string, React.ReactNode> = {
  hard_fact: <Database strokeWidth={1.5} className="w-4 h-4" />,
  soft_fact: <AlignLeft strokeWidth={1.5} className="w-4 h-4" />,
  opinion: <MessageSquare strokeWidth={1.5} className="w-4 h-4" />,
  prediction: <TrendingUp strokeWidth={1.5} className="w-4 h-4" />,
};

export default function ClaimCard({ claim, onMouseEnter, onMouseLeave }: ClaimCardProps) {
  const [open, setOpen] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);
  const [explanationData, setExplanationData] = useState<{
    explanation?: string;
    error_category?: string | null;
  } | null>(null);

  const riskScore = ((claim.verifiability_score ?? 0) * 100).toFixed(0);
  const typeSymbol = TYPE_SYMBOLS[claim.claim_type || ""] || <AlignLeft strokeWidth={1.5} className="w-4 h-4" />;

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
      className="border-b border-outline-variant/20 py-6 group transition-colors hover:bg-surface-container-low/50"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <div className="flex items-start justify-between gap-6 px-4">
        <div className="flex items-start gap-4 flex-1">
          <div className="text-primary mt-0.5 shrink-0">{typeSymbol}</div>
          <div className="flex-1">
            <p className="text-sm font-light leading-relaxed text-on-surface">{claim.text}</p>
            {claim.resolved_text && claim.resolved_text !== claim.text && (
              <p className="text-[11px] text-tertiary mt-1.5 italic">
                → Interpreted as: “{claim.resolved_text}” <span className="opacity-70 not-italic ml-1">(Pronoun resolved)</span>
              </p>
            )}
            {claim.confidence_explanation?.[0] && (
              <p className="text-[11px] text-secondary mt-2 opacity-80">{claim.confidence_explanation[0]}</p>
            )}
            {claim.verification_status === "CONTRADICTED" && (
              <span className="inline-block mt-2 text-[9px] uppercase tracking-wider text-error border border-error/20 bg-error/5 px-2 py-0.5">
                CONTRADICTED
              </span>
            )}
            {claim.verification_status === "UNSUPPORTED" && (
              <span className="inline-block mt-2 text-[9px] uppercase tracking-wider text-outline border border-outline-variant/20 bg-surface-container-low px-2 py-0.5">
                UNSUPPORTED
              </span>
            )}
            {claim.verification_status === "UNVERIFIABLE" && (
              <span className="inline-block mt-2 text-[9px] uppercase tracking-wider text-secondary border border-secondary/20 bg-secondary/5 px-2 py-0.5">
                UNVERIFIABLE
              </span>
            )}
            {claim.verification_status === "SUPPORTED" && (
              <span className="inline-block mt-2 text-[9px] uppercase tracking-wider text-primary border border-primary/20 bg-primary/5 px-2 py-0.5">
                SUPPORTED
              </span>
            )}
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 flex-shrink-0">
          <div className="text-[10px] uppercase font-mono text-outline-variant">{riskScore}% Risk</div>
          <button
            onClick={handleToggle}
            className="text-[10px] uppercase tracking-wider text-primary hover:text-primary-dim transition-colors"
          >
            {open ? "Close" : "Inspect"}
          </button>
        </div>
      </div>

      {open && (
        <div className="mt-6 mx-4 p-6 bg-surface-container-low border border-outline-variant/20 animate-fadeIn">
          <div className="grid grid-cols-3 gap-8 mb-8">
            <div className="space-y-2">
              <div className="flex justify-between text-[9px] uppercase tracking-wider text-outline">
                <span>Model Confidence</span>
                <span>{((claim.score_breakdown?.support ?? 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-surface-variant h-[2px]">
                <div className="bg-tertiary h-full" style={{ width: `${(claim.score_breakdown?.support ?? 0) * 100}%` }} />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-[9px] uppercase tracking-wider text-outline">
                <span>Semantic Match</span>
                <span>{((claim.score_breakdown?.qa_alignment ?? 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-surface-variant h-[2px]">
                <div className="bg-primary h-full" style={{ width: `${(claim.score_breakdown?.qa_alignment ?? 0) * 100}%` }} />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-[9px] uppercase tracking-wider text-outline">
                <span>Conflict</span>
                <span>{((claim.score_breakdown?.contradictions ?? 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-surface-variant h-[2px]">
                <div className="bg-error h-full" style={{ width: `${(claim.score_breakdown?.contradictions ?? 0) * 100}%` }} />
              </div>
            </div>
          </div>

          {claim.evidence && claim.evidence.length > 0 && (
            <div className="space-y-4 mb-6">
              <h5 className="text-[9px] uppercase tracking-widest text-outline">Cross-Referenced Sources</h5>
              <div className="space-y-3">
                {claim.evidence.map((ev, idx) => (
                  <div key={idx} className="flex gap-3 text-xs font-light text-on-surface">
                    <span className="text-secondary">·</span>
                    <div>
                      {ev.url ? (
                        <a href={ev.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                          {ev.domain || ev.source}
                        </a>
                      ) : (
                        <span className="text-on-surface-variant">{ev.domain || ev.source}</span>
                      )}
                      <p className="text-[11px] text-secondary mt-1">&quot;{ev.evidence}&quot;</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="pt-4 border-t border-outline-variant/20">
            {isExplaining ? (
              <div className="animate-pulse space-y-2">
                <div className="h-2 bg-outline-variant/20 w-full" />
                <div className="h-2 bg-outline-variant/20 w-4/5" />
              </div>
            ) : explanationData ? (
              <div className="space-y-2">
                {explanationData.error_category && (
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 border border-error/20 bg-error/5 text-[9px] uppercase tracking-wider mb-2 text-error/90">
                    <AlertCircle strokeWidth={1.5} className="w-3 h-3" />
                    {explanationData.error_category}
                  </span>
                )}
                <p className="text-[11px] leading-relaxed text-on-surface-variant">
                  {explanationData.explanation}
                </p>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}