"use client";

import { useState } from "react";
import Navbar from "../components/Navbar";
import InputBar from "../components/InputBar";
import TrustSummary from "../components/TrustSummary";
import ClaimCard from "../components/ClaimCard";
import FAQ from "../components/FAQ";
import Footer from "../components/Footer";
import { verify } from "../lib/api";

export default function Page() {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hoveredClaimIndex, setHoveredClaimIndex] = useState<number | null>(null);
  const [showUnsafeOverride, setShowUnsafeOverride] = useState(false);
  const [lastMode, setLastMode] = useState<string>("");

  const handleSubmit = async (question: string, answer: string, mode: string) => {
    setIsLoading(true);
    setData(null);
    setShowUnsafeOverride(false);
    setLastMode(mode);
    try {
      const res = await verify(question, answer, mode);
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
        <mark className="bg-accent/15 text-text px-0.5 rounded transition-colors duration-300">
          {highlight}
        </mark>
        {after}
      </>
    );
  };

  return (
    <div className="min-h-screen bg-background text-text font-sans">
      <Navbar />

      <section
        id="hero"
        className="pt-32 pb-20 px-6"
      >
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 text-xs text-trust-high border border-trust-high/30 px-3 py-1 rounded-full mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-trust-high" />
            System Operational
          </div>

          <h1 className="text-4xl md:text-5xl font-light text-primary tracking-tight leading-tight mb-6">
            Verify Any AI Response.
            <br />
            <span className="font-normal">Instantly.</span>
          </h1>

          <p className="text-lg text-textSecondary font-light max-w-xl mx-auto mb-10 leading-relaxed">
            TrustLayer extracts claims from AI outputs, cross-references them
            against real-world evidence, and returns a trust score - so you know
            what to believe.
          </p>

          <button
            onClick={() =>
              document.getElementById("demo")?.scrollIntoView({ behavior: "smooth" })
            }
            className="bg-primary text-background px-8 py-3 rounded text-sm font-normal hover:bg-secondary transition-colors duration-200"
          >
            Try It Live
          </button>
        </div>
      </section>

      <section className="border-y border-border py-10 px-6">
        <div className="max-w-3xl mx-auto grid grid-cols-3 gap-8 text-center">
          {[
            { value: "12+", label: "Verification Signals" },
            { value: "Real-Time", label: "Evidence Retrieval" },
            { value: "Open", label: "Source Architecture" },
          ].map((m, i) => (
            <div key={i}>
              <div className="text-2xl font-light text-primary mb-1">{m.value}</div>
              <div className="text-xs uppercase tracking-wider text-textSecondary">
                {m.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section id="how-it-works" className="py-24 px-6">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-light text-primary tracking-tight mb-16 text-center">
            How It Works
          </h2>

          <div className="grid grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Paste",
                desc: "Enter the AI-generated response you want to verify. Optionally include the original question for deeper analysis.",
              },
              {
                step: "02",
                title: "Analyze",
                desc: "TrustLayer extracts individual claims, classifies each by type, and retrieves evidence from multiple sources.",
              },
              {
                step: "03",
                title: "Trust",
                desc: "Receive a trust score per claim and overall, with source citations, contradiction detection, and risk levels.",
              },
            ].map((s, i) => (
              <div key={i} className="text-center">
                <div className="text-xs text-accent font-medium tracking-wider mb-3">
                  {s.step}
                </div>
                <h3 className="text-lg font-normal text-primary mb-3">{s.title}</h3>
                <p className="text-sm text-textSecondary font-light leading-relaxed">
                  {s.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="features" className="py-24 px-6 border-t border-border">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-light text-primary tracking-tight mb-4 text-center">
            Verification Architecture
          </h2>
          <p className="text-sm text-textSecondary font-light text-center mb-16 max-w-md mx-auto">
            Every claim passes through a multi-stage pipeline.
            No shortcuts. No guesswork.
          </p>

          <div className="grid grid-cols-3 gap-px bg-border rounded-lg overflow-hidden border border-border">
            {[
              {
                icon: "◇",
                title: "Claim Extraction",
                desc: "NLP-powered extraction isolates individual factual claims, opinions, and predictions from any AI response.",
              },
              {
                icon: "◎",
                title: "Evidence Retrieval",
                desc: "Real-time search across knowledge bases. Each claim is matched against retrieved passages using semantic similarity.",
              },
              {
                icon: "△",
                title: "Trust Calibration",
                desc: "Natural Language Inference scores support and contradiction. Claims are risk-scored and calibrated for final trust output.",
              },
            ].map((f, i) => (
              <div key={i} className="bg-surface p-8">
                <div className="text-xl text-accent mb-4">{f.icon}</div>
                <h3 className="text-base font-normal text-primary mb-3">
                  {f.title}
                </h3>
                <p className="text-sm text-textSecondary font-light leading-relaxed">
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="demo" className="py-24 px-6 border-t border-border">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-light text-primary tracking-tight mb-4 text-center">
            Live Verification
          </h2>
          <p className="text-sm text-textSecondary font-light text-center mb-12">
            Paste an AI response below and see the verification pipeline in action.
          </p>

          <div className="space-y-10">
            <InputBar onSubmit={handleSubmit} isLoading={isLoading} />

            {isLoading && (
              <div className="space-y-6 animate-pulse">
                <div className="h-40 bg-surface border border-border rounded-lg shadow-sm" />
                <div className="h-32 bg-surface border border-border rounded-lg shadow-sm" />
                <div className="space-y-4">
                  <div className="h-24 bg-background border border-border rounded-lg shadow-sm" />
                  <div className="h-24 bg-background border border-border rounded-lg shadow-sm" />
                </div>
              </div>
            )}

            {data && (
              !data.is_safe && !showUnsafeOverride ? (
                <div className="border border-trust-low/30 bg-trust-low/5 rounded-lg p-10 text-center space-y-5 shadow-sm animate-fadeIn">
                  <div className="text-3xl text-trust-low">△</div>
                  <div>
                    <h2 className="text-xl text-trust-low font-normal mb-1">
                      This response may be unreliable
                    </h2>
                    <p className="text-sm text-trust-low/70 font-light">
                      High epistemic risk or internal contradictions detected.
                    </p>
                  </div>
                  <button
                    onClick={() => setShowUnsafeOverride(true)}
                    className="mt-4 text-sm border border-trust-low/30 text-trust-low px-6 py-2 rounded hover:bg-trust-low/5 transition-colors duration-200"
                  >
                    View anyway
                  </button>
                </div>
              ) : (
                <div className="space-y-10 animate-fadeIn">
                  <TrustSummary data={data} mode={lastMode} />

                  <div className="border border-border rounded-lg p-8 bg-surface shadow-sm transition-all duration-300">
                    <h2 className="text-xs uppercase tracking-widest text-textSecondary font-medium mb-4">
                      Verified Response
                    </h2>
                    <p className="text-base text-text leading-relaxed font-light whitespace-pre-wrap">
                      {renderOriginalText()}
                    </p>
                  </div>

                  <div className="space-y-4">
                    {data.claims.map((c: any, i: number) => (
                      <div
                        key={i}
                        className="opacity-0 animate-fadeIn"
                        style={{ animationDelay: `${i * 80}ms` }}
                      >
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
      </section>

      <section className="py-24 px-6 border-t border-border">
        <FAQ />
      </section>

      <Footer />
    </div>
  );
}