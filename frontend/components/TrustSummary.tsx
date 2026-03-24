"use client";

interface TrustSummaryProps {
  data: {
    overall_trust_score: number;
    signals?: {
      qa_relevance?: number;
      epistemic_trust?: number;
      epistemic_risk?: number;
    };
    summary_bullets?: string[];
    is_safe?: boolean;
  };
  mode?: string;
}

export default function TrustSummary({ data, mode }: TrustSummaryProps) {
  const score = data.overall_trust_score;
  const pct = Math.round(score * 100);

  const circumference = 283;
  const offset = circumference - (circumference * score);

  let verdict = "Likely Unreliable";
  let ringColor = "#8b4f4f";
  let verdictColor = "text-trust-low";

  if (score >= 0.7) {
    verdict = "Mostly Reliable";
    ringColor = "#3d6b4f";
    verdictColor = "text-trust-high";
  } else if (score >= 0.4) {
    verdict = "Proceed with Caution";
    ringColor = "#8b7355";
    verdictColor = "text-trust-medium";
  }

  const formatBullet = (b: string) => {
    if (b.startsWith("✔")) return { symbol: "→", text: b.slice(2), color: "text-trust-high" };
    if (b.startsWith("❌")) return { symbol: "×", text: b.slice(2), color: "text-trust-low" };
    if (b.startsWith("⚠")) return { symbol: "—", text: b.slice(2), color: "text-trust-medium" };
    return { symbol: "·", text: b, color: "text-textSecondary" };
  };

  return (
    <div className="border border-border rounded-lg p-8 bg-surface shadow-sm">
      <div className="flex items-start justify-between mb-6">
        <h2 className="text-xs uppercase tracking-widest text-textSecondary font-medium">
          Verification Result
        </h2>
        {mode && (
          <span className="text-xs text-textSecondary/60 border border-border px-2 py-0.5 rounded">
            {mode === "fast" ? "Quick Scan" : "Deep Analysis"}
          </span>
        )}
      </div>

      <div className="flex items-center gap-10">
        <div className="relative flex-shrink-0">
          <svg width="120" height="120" viewBox="0 0 100 100" className="trust-ring">
            <circle cx="50" cy="50" r="45" className="trust-ring-track" />
            <circle
              cx="50"
              cy="50"
              r="45"
              className="trust-ring-fill animate-ringFill"
              stroke={ringColor}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-light text-primary">{pct}</span>
            <span className="text-[10px] uppercase tracking-wider text-textSecondary">Trust</span>
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className={`text-lg font-normal mb-4 ${verdictColor}`}>{verdict}</div>

          <div className="space-y-2">
            {data.summary_bullets?.map((b, i) => {
              const { symbol, text, color } = formatBullet(b);
              return (
                <div key={i} className="flex items-start gap-2.5 text-sm">
                  <span className={`${color} font-medium flex-shrink-0 w-3 text-center`}>{symbol}</span>
                  <span className="text-text font-light">{text}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {data.signals && (
        <div className="mt-8 pt-6 border-t border-border grid grid-cols-2 gap-6">
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs text-textSecondary">
              <span>Response Relevance</span>
              <span>{Math.round((data.signals.qa_relevance ?? 0) * 100)}%</span>
            </div>
            <div className="w-full bg-background rounded-full h-1 overflow-hidden border border-border">
              <div
                className="bg-accent h-full rounded-full transition-all duration-700"
                style={{ width: `${(data.signals.qa_relevance ?? 0) * 100}%` }}
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs text-textSecondary">
              <span>Factual Confidence</span>
              <span>{Math.round((data.signals.epistemic_trust ?? 0) * 100)}%</span>
            </div>
            <div className="w-full bg-background rounded-full h-1 overflow-hidden border border-border">
              <div
                className="bg-accent h-full rounded-full transition-all duration-700"
                style={{ width: `${(data.signals.epistemic_trust ?? 0) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}