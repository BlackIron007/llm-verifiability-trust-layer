"use client";

import InputBar from "../components/InputBar";
import TrustSummary from "../components/TrustSummary";
import ClaimCard from "../components/ClaimCard";
import { useState } from "react";
import { verify } from "../lib/api";

export default function Page() {
  const [data, setData] = useState(null);

  const handleSubmit = async (text) => {
    const res = await verify(text);
    setData(res);
  };

  return (
    <div className="min-h-screen bg-[#fffef9] text-[#2c2218] px-6 py-10">
      <div className="max-w-4xl mx-auto space-y-8">
        <InputBar onSubmit={handleSubmit} />

        {data && (
          <>
            <TrustSummary data={data} />

            <div className="space-y-4">
              {data.claims.map((c, i) => (
                <ClaimCard key={i} claim={c} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}