"use client";

import { useState } from "react";

export default function InputBar({ onSubmit, isLoading }) {
  const [text, setText] = useState("");
  const [isFast, setIsFast] = useState(true);

  return (
    <div className="border border-border rounded-lg p-6 bg-surface shadow-sm transition-shadow hover:shadow-md">
      <textarea
        className="w-full bg-transparent outline-none text-base placeholder-textSecondary text-text leading-relaxed resize-none"
        placeholder="Enter text to verify..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={4}
      />

      <div className="flex justify-between items-center mt-4">
        <div className="flex items-center gap-1 bg-background p-1 rounded-md border border-border">
          <button
            onClick={() => setIsFast(true)}
            className={`px-3 py-1.5 text-xs rounded transition-all duration-200 ${isFast ? 'bg-surface shadow-sm text-text font-medium' : 'text-textSecondary hover:text-text'}`}
          >
            ⚡ Fast
          </button>
          <button
            onClick={() => setIsFast(false)}
            className={`px-3 py-1.5 text-xs rounded transition-all duration-200 ${!isFast ? 'bg-surface shadow-sm text-text font-medium' : 'text-textSecondary hover:text-text'}`}
          >
            🔬 Deep
          </button>
        </div>
        <button
          onClick={() => onSubmit(text, isFast ? "fast" : "full")}
          disabled={isLoading || !text.trim()}
          className={`text-sm border border-border px-6 py-2 rounded transition-colors duration-200 ${isLoading || !text.trim() ? 'opacity-50 cursor-not-allowed text-textSecondary' : 'text-text hover:bg-border'}`}
        >
          {isLoading ? "Analyzing..." : "Analyze"}
        </button>
      </div>
    </div>
  );
}