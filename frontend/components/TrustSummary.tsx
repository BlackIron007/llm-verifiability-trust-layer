"use client";

import { Check, AlertCircle, Minus } from "lucide-react";

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
}

export default function TrustSummary({ data }: TrustSummaryProps) {
  const score = data.overall_trust_score;
  const pct = Math.round(score * 100);

  const ringStyle = {
    background: `conic-gradient(#715b3e 0% ${pct}%, #ebe2cb ${pct}% 100%)`,
  };

  const formatBullet = (b: string) => {
    if (b.startsWith("✔")) return { symbol: <Check strokeWidth={1.5} className="w-4 h-4 text-emerald-600" />, text: b.slice(2), bg: "" };
    if (b.startsWith("❌")) return { symbol: <AlertCircle strokeWidth={1.5} className="w-4 h-4 text-red-600" />, text: b.slice(2), bg: "text-error/80" };
    if (b.startsWith("⚠")) return { symbol: <Minus strokeWidth={1.5} className="w-4 h-4 text-on-surface-variant" />, text: b.slice(2), bg: "" };
    return { symbol: <Minus strokeWidth={1.5} className="w-4 h-4 text-on-surface-variant" />, text: b, bg: "" };
  };

  return (
    <div className="grid grid-cols-2 gap-px bg-outline-variant/10 border border-outline-variant/10">
      <div className="bg-surface-container p-8 flex flex-col items-center justify-center gap-4">
        <div className="relative w-32 h-32 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full opacity-20" style={ringStyle}></div>
          <div className="text-center">
            <div className="text-3xl font-light tracking-tighter">{pct}%</div>
            <div className="text-[10px] uppercase tracking-widest text-secondary">Confidence</div>
          </div>
        </div>
      </div>

      <div className="bg-surface-container p-8">
        <h4 className="text-[10px] uppercase text-outline mb-4">Evidence Log</h4>
        <ul className="space-y-3 text-xs font-light text-on-surface">
          {data.summary_bullets?.map((b, i) => {
            const { symbol, text, bg } = formatBullet(b);
            return (
              <li key={i} className="flex items-start gap-3">
                <div className="mt-0.5 shrink-0">{symbol}</div>
                <span className={bg || "text-on-surface"}>{text}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}