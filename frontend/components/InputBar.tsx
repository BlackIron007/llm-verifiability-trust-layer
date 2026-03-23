"use client";

import { useState } from "react";

export default function InputBar({ onSubmit }) {
  const [text, setText] = useState("");

  return (
    <div className="border border-[#e8e2d8] rounded-xl p-4 bg-[#faf8f3]">
      <textarea
        className="w-full bg-transparent outline-none text-sm placeholder-[#6b5d4f]"
        placeholder="Enter text to verify..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <div className="flex justify-between items-center mt-3">
        <span className="text-xs text-[#6b5d4f]">Fast Mode</span>
        <button
          onClick={() => onSubmit(text)}
          className="text-sm border border-[#e8e2d8] px-4 py-1 rounded-lg hover:bg-[#faf8f3]"
        >
          Analyze
        </button>
      </div>
    </div>
  );
}