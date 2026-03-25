"use client";

import { FileSearch, Network, Scale, ShieldCheck, ChevronDown, Lock, Cpu, Shield } from "lucide-react";
import Link from "next/link";

export default function LandingPage() {
  const faqs = [
    { q: "What is QA Alignment?", a: "QA Alignment measures how accurately the model's generated response aligns with the verified facts retrieved from external datastores. It's essentially a deterministic truth score." },
    { q: "How fast is Deep Analysis compared to Quick Scan?", a: "Quick Scan relies on streamlined API evaluations and typically resolves very quickly. Deep Analysis executes broader multi-query external searches and heavier Natural Language Inference algorithms for comprehensive fact resolution." },
    { q: "Does Veritas AI store my prompts?", a: "No. All agent inputs and model responses are processed statelessly in-memory and dropped immediately after verification completes. Only anonymized trust scores are persisted for audit logs." },
    { q: "What types of claims can Veritas AI verify?", a: "Veritas AI classifies claims into four types: hard facts (verifiable against databases), soft facts (requiring contextual evaluation), predictions (future-oriented statements), and opinions (subjective, not fact-checkable)." },
    { q: "Can I integrate Veritas AI into my own pipeline?", a: "Yes. Veritas AI exposes a RESTful API with batch, streaming, and single-shot verification endpoints. Authenticated via API key, it can be embedded into any LLM orchestration workflow." }
  ];

  return (
    <div className="min-h-screen flex flex-col font-sans bg-background">
      <nav className="fixed top-0 w-full z-50 bg-[#fff9ee]/90 dark:bg-stone-900/90 backdrop-blur-md border-b border-[#b9b29c]/15">
        <div className="flex justify-between items-center px-12 h-16 w-full max-w-[1600px] mx-auto">
          <div className="flex items-center gap-2 text-primary dark:text-[#ebe2cb]">
            <ShieldCheck strokeWidth={1.5} className="w-5 h-5" />
            <div className="text-lg font-normal tracking-tighter">Veritas AI</div>
          </div>

          <div className="hidden md:flex gap-8 items-center">
            <Link href="/dashboard" className="font-light tracking-tight text-sm uppercase text-primary dark:text-[#ebe2cb] hover:opacity-70 transition-opacity">Dashboard</Link>
          </div>
        </div>
      </nav>

      <main className="flex-grow pt-28 pb-20 flex flex-col items-center w-full max-w-5xl mx-auto px-6">

        <div className="w-full max-w-3xl text-center mb-20 animate-fadeIn">
          <h1 className="text-4xl sm:text-5xl font-light tracking-tighter text-on-background mb-6 leading-tight">
            Stop <span className="text-tertiary">Hallucinations</span> Before They Deploy.
          </h1>
          <p className="border border-outline-variant/15 bg-surface-container-low p-6 text-base sm:text-lg text-secondary leading-relaxed font-light shadow-sm mb-10">
            Veritas AI acts as a determinism engine between your generative AI models and your users. We evaluate semantic claims against grounded truth to ensure absolute reliability in enterprise production environments.
          </p>
          <Link
            href="/dashboard"
            className="inline-block bg-primary text-on-primary px-10 py-4 text-sm tracking-widest uppercase font-light hover:bg-primary-dim shadow-md transition-all"
          >
            Try it Now &rarr;
          </Link>
        </div>

        <section className="w-full mt-8 mb-20 animate-fadeIn" style={{ animationDelay: "200ms", animationFillMode: "both" }}>
          <h2 className="text-3xl font-light text-center text-on-background mb-14 tracking-tighter">How the Verification Pipeline Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 text-center md:text-left">
            <div className="space-y-4">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary mx-auto md:mx-0">
                <FileSearch strokeWidth={1.5} className="w-5 h-5" />
              </div>
              <h5 className="text-xs uppercase font-medium tracking-wider text-on-surface">Claim Extraction</h5>
              <p className="text-sm leading-relaxed font-light text-secondary">
                Uses a dedicated processing pipeline to decompose complex text responses into granular, verifiable atomic statements.
              </p>
            </div>
            <div className="space-y-4">
              <div className="w-10 h-10 rounded-full bg-tertiary/10 flex items-center justify-center text-tertiary mx-auto md:mx-0">
                <Network strokeWidth={1.5} className="w-5 h-5" />
              </div>
              <h5 className="text-xs uppercase font-medium tracking-wider text-on-surface">Evidence Retrieval</h5>
              <p className="text-sm leading-relaxed font-light text-secondary">
                Executes targeted logic queries via Google Custom Search APIs and internal vector databases to gather strict factual consensus.
              </p>
            </div>
            <div className="space-y-4">
              <div className="w-10 h-10 rounded-full bg-error/10 flex items-center justify-center text-error mx-auto md:mx-0">
                <Scale strokeWidth={1.5} className="w-5 h-5" />
              </div>
              <h5 className="text-xs uppercase font-medium tracking-wider text-on-surface">Trust Calibration</h5>
              <p className="text-sm leading-relaxed font-light text-secondary">
                Applies Natural Language Inference (NLI) models and zero-shot reasoning evaluations to output deterministic confidence scores.
              </p>
            </div>
          </div>
        </section>

        <div className="w-full border-t border-outline-variant/10 my-4"></div>

        <section id="privacy" className="w-full mt-16 mb-16 scroll-mt-24 animate-fadeIn" style={{ animationDelay: "300ms", animationFillMode: "both" }}>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-9 h-9 rounded-full bg-tertiary/10 flex items-center justify-center text-tertiary">
              <Lock strokeWidth={1.5} className="w-4 h-4" />
            </div>
            <h2 className="text-2xl font-light tracking-tighter text-on-background">Privacy</h2>
          </div>
          <div className="bg-surface border border-outline-variant/15 p-8 space-y-4">
            <p className="text-base font-light leading-relaxed text-secondary">
              Veritas AI operates on a <strong className="text-on-surface font-medium">zero-retention architecture</strong>. All agent inputs and model responses are processed entirely in-memory and are never written to disk or transmitted to third parties.
            </p>
            <ul className="space-y-3 text-sm font-light text-secondary list-none">
              <li className="flex items-start gap-2"><span className="text-tertiary mt-0.5">·</span> No cookies, no tracking pixels, no analytics SDKs</li>
              <li className="flex items-start gap-2"><span className="text-tertiary mt-0.5">·</span> Prompt data is dropped immediately after verification completes</li>
              <li className="flex items-start gap-2"><span className="text-tertiary mt-0.5">·</span> Only anonymized trust scores are persisted for audit logging</li>
              <li className="flex items-start gap-2"><span className="text-tertiary mt-0.5">·</span> No user accounts or personally identifiable information collected</li>
            </ul>
          </div>
        </section>

        <section id="security" className="w-full mb-16 scroll-mt-24 animate-fadeIn" style={{ animationDelay: "400ms", animationFillMode: "both" }}>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <Shield strokeWidth={1.5} className="w-4 h-4" />
            </div>
            <h2 className="text-2xl font-light tracking-tighter text-on-background">Security</h2>
          </div>
          <div className="bg-surface border border-outline-variant/15 p-8 space-y-4">
            <p className="text-base font-light leading-relaxed text-secondary">
              Every API interaction is authenticated and rate-limited. The system is hardened against abuse with multiple layers of input validation.
            </p>
            <ul className="space-y-3 text-sm font-light text-secondary list-none">
              <li className="flex items-start gap-2"><span className="text-primary mt-0.5">·</span> Token-based authentication on all endpoints</li>
              <li className="flex items-start gap-2"><span className="text-primary mt-0.5">·</span> Adaptive rate limiting to prevent abuse</li>
              <li className="flex items-start gap-2"><span className="text-primary mt-0.5">·</span> Request payload size validation with hard caps</li>
              <li className="flex items-start gap-2"><span className="text-primary mt-0.5">·</span> Strict origin whitelisting (CORS)</li>
              <li className="flex items-start gap-2"><span className="text-primary mt-0.5">·</span> No secrets exposed in client-side bundles</li>
            </ul>
          </div>
        </section>

        <section id="architecture" className="w-full mb-16 scroll-mt-24 animate-fadeIn" style={{ animationDelay: "500ms", animationFillMode: "both" }}>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-9 h-9 rounded-full bg-error/10 flex items-center justify-center text-error">
              <Cpu strokeWidth={1.5} className="w-4 h-4" />
            </div>
            <h2 className="text-2xl font-light tracking-tighter text-on-background">Architecture</h2>
          </div>
          <div className="bg-surface border border-outline-variant/15 p-8 space-y-4">
            <p className="text-base font-light leading-relaxed text-secondary">
              A modular, high-throughput pipeline designed for sub-second verification latency at scale.
            </p>
            <ul className="space-y-3 text-sm font-light text-secondary list-none">
              <li className="flex items-start gap-2"><span className="text-error mt-0.5">·</span> FastAPI backend with async request handling</li>
              <li className="flex items-start gap-2"><span className="text-error mt-0.5">·</span> Parallel processing for concurrent claim classification and evidence retrieval</li>
              <li className="flex items-start gap-2"><span className="text-error mt-0.5">·</span> NLI pipeline for Natural Language Inference (support / contradict / neutral)</li>
              <li className="flex items-start gap-2"><span className="text-error mt-0.5">·</span> Real-time evidence retrieval via external search APIs and vector databases</li>
              <li className="flex items-start gap-2"><span className="text-error mt-0.5">·</span> Semantic similarity embeddings for evidence-claim alignment</li>
              <li className="flex items-start gap-2"><span className="text-error mt-0.5">·</span> Evidence caching layer to eliminate redundant API calls</li>
              <li className="flex items-start gap-2"><span className="text-error mt-0.5">·</span> Coreference resolution for pronoun disambiguation across claim chains</li>
            </ul>
          </div>
        </section>

        <div className="w-full border-t border-outline-variant/10 my-4"></div>

        <section className="w-full mt-12 mb-20 animate-fadeIn" style={{ animationDelay: "600ms", animationFillMode: "both" }}>
          <h2 className="text-3xl font-light text-center text-on-background mb-10 tracking-tighter">Frequently Asked Questions</h2>
          <div className="flex flex-col gap-3 max-w-3xl mx-auto">
            {faqs.map((faq, i) => (
              <details key={i} className="group border border-outline-variant/20 bg-surface p-6 shadow-sm">
                <summary className="flex justify-between items-center font-medium text-base text-on-surface list-none outline-none cursor-pointer">
                  {faq.q}
                  <span className="text-tertiary group-open:rotate-180 transition-transform duration-300">
                    <ChevronDown strokeWidth={1.5} className="w-4 h-4" />
                  </span>
                </summary>
                <p className="mt-4 text-sm font-light leading-relaxed text-secondary border-t border-outline-variant/10 pt-4">
                  {faq.a}
                </p>
              </details>
            ))}
          </div>
        </section>
      </main>

      <footer className="w-full border-t border-[#b9b29c]/15 bg-[#fff9ee] dark:bg-stone-950">
        <div className="flex justify-between items-center px-12 py-8 w-full max-w-[1600px] mx-auto">
          <span className="text-[10px] font-normal tracking-[0.05em] uppercase text-[#817a67] dark:text-[#b9b29c]">© 2026 Veritas AI. All Rights Reserved.</span>
          <div className="flex gap-8">
            <a href="#privacy" className="text-[10px] font-normal tracking-[0.05em] uppercase text-[#817a67] dark:text-[#b9b29c] hover:text-[#715b3e] transition-colors">Privacy</a>
            <a href="#security" className="text-[10px] font-normal tracking-[0.05em] uppercase text-[#817a67] dark:text-[#b9b29c] hover:text-[#715b3e] transition-colors">Security</a>
            <a href="#architecture" className="text-[10px] font-normal tracking-[0.05em] uppercase text-[#817a67] dark:text-[#b9b29c] hover:text-[#715b3e] transition-colors">Architecture</a>
          </div>
        </div>
      </footer>
    </div>
  );
}