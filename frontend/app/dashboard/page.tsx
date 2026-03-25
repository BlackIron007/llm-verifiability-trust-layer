"use client";

import { useState, useEffect } from "react";
import TrustSummary from "../../components/TrustSummary";
import ClaimCard from "../../components/ClaimCard";
import { verify, fetchRecentVerifications } from "../../lib/api";
import { CheckCircle2, ShieldCheck } from "lucide-react";
import Link from "next/link";

interface RecentVerification {
  id: number;
  input_text: string;
  trust_score: number;
  mode: string;
  created_at: string;
}

export default function DashboardPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [mode, setMode] = useState<"fast" | "full">("fast");

  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hoveredClaimIndex, setHoveredClaimIndex] = useState<number | null>(null);
  const [recentVerifications, setRecentVerifications] = useState<RecentVerification[]>([]);

  const canSubmit = answer.trim().length > 0 && !isLoading;

  useEffect(() => {
    fetchRecentVerifications().then(setRecentVerifications).catch(() => { });
  }, []);

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setIsLoading(true);
    setData(null);
    try {
      const res = await verify(question, answer, mode);
      setData(res);
      fetchRecentVerifications().then(setRecentVerifications).catch(() => { });
    } catch (error) {
      console.error("Verification failed:", error);
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
        <mark className="bg-primary/15 text-on-surface px-0.5 rounded transition-colors duration-300">
          {highlight}
        </mark>
        {after}
      </>
    );
  };

  const formatTimestamp = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "--:--";
    }
  };

  return (
    <div className="min-h-screen flex flex-col font-sans bg-background">
      <nav className="fixed top-0 w-full z-50 bg-[#fff9ee]/90 dark:bg-stone-900/90 backdrop-blur-md border-b border-[#b9b29c]/15">
        <div className="flex justify-between items-center px-12 h-16 w-full max-w-[1600px] mx-auto">
          <Link href="/" className="flex items-center gap-2 text-primary dark:text-[#ebe2cb] hover:opacity-80 transition-opacity">
            <ShieldCheck strokeWidth={1.5} className="w-5 h-5" />
            <div className="text-lg font-normal tracking-tighter">Veritas AI</div>
          </Link>

          <div className="hidden md:flex gap-8 items-center">
            <span className="font-light tracking-tight text-sm uppercase text-primary dark:text-[#ebe2cb] border-b border-primary pb-1">Dashboard</span>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 dark:bg-[#1a2f24] rounded-full">
              <CheckCircle2 strokeWidth={1.5} className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
              <span className="font-light tracking-tight text-[10px] uppercase text-emerald-700 dark:text-emerald-400">System Operational</span>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-grow pt-28 pb-20 flex flex-col items-center w-full max-w-5xl mx-auto px-6">

        <section className="w-full flex justify-between items-center bg-surface-container-low px-12 py-6 mb-8 border border-outline-variant/15 animate-fadeIn">
          <div className="flex flex-col items-center">
            <p className="text-[9px] uppercase text-outline mb-1 tracking-widest">Verification Signals</p>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-light tracking-tighter text-on-surface">12+</span>
              <span className="text-[9px] text-emerald-600 uppercase font-medium">Active</span>
            </div>
          </div>
          <div className="w-px h-10 bg-outline-variant/20"></div>
          <div className="flex flex-col items-center">
            <p className="text-[9px] uppercase text-outline mb-1 tracking-widest">Decision Accuracy</p>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-light tracking-tighter text-on-surface">99.8%</span>
              <span className="text-[9px] text-tertiary uppercase font-medium">Stable</span>
            </div>
          </div>
          <div className="w-px h-10 bg-outline-variant/20"></div>
          <div className="flex flex-col items-center">
            <p className="text-[9px] uppercase text-outline mb-1 tracking-widest">Verification Latency</p>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-light tracking-tighter text-on-surface">14ms</span>
              <span className="text-[9px] text-secondary uppercase font-medium">p95</span>
            </div>
          </div>
        </section>

        <section className="w-full bg-surface p-10 sm:p-14 flex flex-col gap-10 border border-outline-variant/15 shadow-sm animate-fadeIn" style={{ animationDelay: "100ms", animationFillMode: "both" }}>
          <header className="flex justify-between items-end">
            <div>
              <h1 className="text-4xl font-light tracking-tighter text-on-background animate-fadeIn">Veritas Operations Dashboard</h1>
              <p className="text-sm text-secondary font-light mt-2 animate-fadeIn" style={{ animationDelay: "100ms" }}>Intentional AI verification across distributed datasets.</p>
            </div>
            <div className="flex border border-outline-variant/30 p-1 bg-surface-container-low animate-fadeIn" style={{ animationDelay: "200ms" }}>
              <button
                onClick={() => setMode("fast")}
                className={`px-4 py-1.5 text-[10px] uppercase font-medium transition-colors ${mode === "fast" ? "bg-primary text-on-primary" : "text-outline hover:text-primary"
                  }`}
              >
                Quick Scan
              </button>
              <button
                onClick={() => setMode("full")}
                className={`px-4 py-1.5 text-[10px] uppercase font-medium transition-colors ${mode === "full" ? "bg-primary text-on-primary" : "text-outline hover:text-primary"
                  }`}
              >
                Deep Analysis
              </button>
            </div>
          </header>

          <div className="grid gap-8 mt-4">
            <div className="space-y-2 animate-fadeIn" style={{ animationDelay: "150ms", animationFillMode: "both" }}>
              <label className="text-[10px] font-normal tracking-[0.05em] uppercase text-outline">Agent Input</label>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="w-full min-h-[100px] border border-outline-variant/20 bg-surface-container-low p-4 text-sm font-light resize-none focus:outline-none focus:border-primary/50 placeholder:text-outline-variant/50 transition-colors"
                placeholder="Paste the claim or prompt here (Optional)..."
              />
            </div>
            <div className="space-y-2 animate-fadeIn" style={{ animationDelay: "250ms", animationFillMode: "both" }}>
              <label className="text-[10px] font-normal tracking-[0.05em] uppercase text-outline">Model Response</label>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                className="w-full min-h-[140px] border border-outline-variant/20 bg-surface-container-low p-4 text-sm font-light resize-none focus:outline-none focus:border-primary/50 placeholder:text-outline-variant/50 transition-colors"
                placeholder="Paste the AI-generated response for verification..."
              />
            </div>
            <button
              onClick={handleSubmit}
              disabled={!canSubmit}
              className={`w-full py-4 text-sm tracking-widest uppercase font-light transition-all flex justify-center items-center gap-3 animate-fadeIn border border-transparent ${canSubmit
                ? "bg-primary text-on-primary hover:bg-primary-dim shadow-md"
                : "bg-surface-container-low border-outline-variant/20 text-outline cursor-not-allowed"}`}
              style={{ animationDelay: "350ms", animationFillMode: "both" }}
            >
              {isLoading ? "Verifying Context..." : "Verify Response Integrity \u2192"}
            </button>
          </div>

          {isLoading && (
            <div className="space-y-6 pt-4 animate-pulse">
              <div className="h-40 bg-surface-variant border border-outline-variant/10" />
              <div className="h-32 bg-surface-variant border border-outline-variant/10" />
            </div>
          )}

          {data && (
            <div className="space-y-10 animate-fadeIn pt-4 border-t border-outline-variant/15 mt-6">
              <TrustSummary data={data} />

              <div className="bg-surface-container-low p-8 border border-outline-variant/20">
                <h4 className="text-[10px] uppercase text-outline mb-4 tracking-widest">Verified Passages</h4>
                <p className="text-sm text-on-surface leading-relaxed font-light whitespace-pre-wrap">
                  {renderOriginalText()}
                </p>
              </div>

              <div className="space-y-0 border-t border-outline-variant/20">
                {data.claims.map((c: any, i: number) => (
                  <div key={i} className="animate-fadeIn" style={{ animationDelay: `${i * 100}ms`, animationFillMode: "both" }}>
                    <ClaimCard
                      claim={c}
                      onMouseEnter={() => setHoveredClaimIndex(i)}
                      onMouseLeave={() => setHoveredClaimIndex(null)}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        <section className="w-full mt-6 bg-surface-container-low p-8 border border-outline-variant/15 animate-fadeIn" style={{ animationDelay: "300ms", animationFillMode: "both" }}>
          <h3 className="text-[10px] font-normal tracking-[0.05em] uppercase text-outline mb-6">Recent Verifications</h3>
          <div className="flex flex-col gap-1">
            {recentVerifications.length > 0 ? (
              recentVerifications.map((v) => {
                const trustPct = Math.round(v.trust_score * 100);
                const isLow = v.trust_score < 0.5;
                const colorClass = isLow ? "text-error" : "text-tertiary";
                const statusLabel = isLow ? "Low Confidence" : "Verified";
                return (
                  <div key={v.id} className="bg-surface py-4 px-6 flex flex-col gap-1 border border-outline-variant/10">
                    <div className="flex justify-between items-center">
                      <span className={`text-[9px] font-mono uppercase ${colorClass}`}>{statusLabel} — {trustPct}%</span>
                      <span className="text-[9px] text-outline-variant">{formatTimestamp(v.created_at)}</span>
                    </div>
                    <div className="text-[10px] font-light tracking-tight text-on-surface truncate max-w-[600px]">
                      {v.input_text}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="bg-surface-container-low py-8 flex flex-col items-center justify-center opacity-50 border border-dashed border-outline-variant/30">
                <span className="text-[9px] font-mono text-tertiary uppercase mb-2">Awaiting Input</span>
                <span className="text-xs text-outline font-light">Engine is idle. Paste a claim to begin verification.</span>
              </div>
            )}
          </div>
        </section>
      </main>

      <footer className="w-full border-t border-[#b9b29c]/15 bg-[#fff9ee] dark:bg-stone-950">
        <div className="flex justify-between items-center px-12 py-8 w-full max-w-[1600px] mx-auto">
          <span className="text-[10px] font-normal tracking-[0.05em] uppercase text-[#817a67] dark:text-[#b9b29c]">© 2026 Veritas AI. All Rights Reserved.</span>
          <div className="flex gap-8">
            <Link href="/#privacy" className="text-[10px] font-normal tracking-[0.05em] uppercase text-[#817a67] dark:text-[#b9b29c] hover:text-[#715b3e] transition-colors">Privacy</Link>
            <Link href="/#security" className="text-[10px] font-normal tracking-[0.05em] uppercase text-[#817a67] dark:text-[#b9b29c] hover:text-[#715b3e] transition-colors">Security</Link>
            <Link href="/#architecture" className="text-[10px] font-normal tracking-[0.05em] uppercase text-[#817a67] dark:text-[#b9b29c] hover:text-[#715b3e] transition-colors">Architecture</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
