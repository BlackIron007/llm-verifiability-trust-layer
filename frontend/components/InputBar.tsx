"use client";

import { useState } from "react";

interface InputBarProps {
  onSubmit: (question: string, answer: string, mode: string) => void;
  isLoading: boolean;
}

export default function InputBar({ onSubmit, isLoading }: InputBarProps) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [mode, setMode] = useState<"fast" | "full">("full");

  const canSubmit = answer.trim().length > 0 && !isLoading;

  return (
    <div className="border border-border rounded-lg bg-surface shadow-sm transition-shadow hover:shadow-md">
      {/* Question field */}
      <div className="px-6 pt-5 pb-3 border-b border-border/60">
        <label className="text-xs uppercase tracking-wider text-textSecondary/70 font-medium mb-2 block">
          Question (optional)
        </label>
        <input
          type="text"
          className="w-full bg-transparent outline-none text-sm placeholder-textSecondary/50 text-text font-light"
          placeholder="What question was the AI asked?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
      </div>

      {/* Answer field */}
      <div className="px-6 pt-4 pb-4">
        <label className="text-xs uppercase tracking-wider text-textSecondary/70 font-medium mb-2 block">
          AI Response
        </label>
        <textarea
          className="w-full bg-transparent outline-none text-base placeholder-textSecondary/50 text-text leading-relaxed resize-none font-light"
          placeholder="Paste the AI response to verify..."
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          rows={4}
        />
      </div>

      {/* Controls */}
      <div className="flex justify-between items-center px-6 pb-5">
        {/* Mode toggle */}
        <div className="flex items-center gap-1 bg-background p-1 rounded-md border border-border">
          <button
            onClick={() => setMode("fast")}
            className={`px-3 py-1.5 text-xs rounded transition-all duration-200 ${
              mode === "fast"
                ? "bg-surface shadow-sm text-text font-medium"
                : "text-textSecondary hover:text-text"
            }`}
            title="Surface-level check, faster results"
          >
            Quick Scan
          </button>
          <button
            onClick={() => setMode("full")}
            className={`px-3 py-1.5 text-xs rounded transition-all duration-200 ${
              mode === "full"
                ? "bg-surface shadow-sm text-text font-medium"
                : "text-textSecondary hover:text-text"
            }`}
            title="Full evidence verification, thorough analysis"
          >
            Deep Analysis
          </button>
        </div>

        <button
          onClick={() => onSubmit(question, answer, mode)}
          disabled={!canSubmit}
          className={`text-sm px-6 py-2 rounded transition-all duration-200 ${
            canSubmit
              ? "bg-primary text-background hover:bg-secondary"
              : "border border-border opacity-40 cursor-not-allowed text-textSecondary"
          }`}
        >
          {isLoading ? "Analyzing..." : "Verify"}
        </button>
      </div>
    </div>
  );
}