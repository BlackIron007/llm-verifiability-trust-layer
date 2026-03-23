"use client";

import { useState } from "react";

export default function InputBar({ onSubmit }) {
  const [text, setText] = useState("");

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
        <span className="text-sm text-textSecondary font-light">Fast Mode</span>
        <button
          onClick={() => onSubmit(text)}
          className="text-sm border border-border px-6 py-2 rounded text-text hover:bg-border transition-colors duration-200"
        >
          Analyze
        </button>
      </div>
    </div>
  );
}