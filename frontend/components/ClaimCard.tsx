"use client";

import { useState } from "react";

export default function ClaimCard({ claim }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-[#e8e2d8] rounded-xl p-4 bg-white">
      <div className="flex justify-between">
        <p className="text-sm">{claim.text}</p>
        <span className="text-xs text-[#6b5d4f]">
          {(claim.verifiability_score * 100).toFixed(0)}%
        </span>
      </div>

      <div className="mt-2 text-xs text-[#6b5d4f]">
        {claim.confidence_explanation?.[0]}
      </div>

      <button
        onClick={() => setOpen(!open)}
        className="mt-3 text-xs underline"
      >
        {open ? "Hide" : "Why?"}
      </button>

      {open && (
        <div className="mt-3 text-xs space-y-2">
          <div>
            Support: {claim.score_breakdown?.support}
          </div>
          <div>
            QA: {claim.score_breakdown?.qa_alignment}
          </div>
        </div>
      )}
    </div>
  );
}