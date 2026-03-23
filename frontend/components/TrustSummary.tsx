export default function TrustSummary({ data }) {
  const score = data.overall_trust_score;

  return (
    <div className="border border-[#e8e2d8] rounded-xl p-5 bg-[#faf8f3]">
      <h2 className="text-lg font-light">Trust Summary</h2>

      <div className="mt-2 text-sm text-[#6b5d4f]">
        Score: {(score * 100).toFixed(0)}%
      </div>

      <div className="mt-3 space-y-1 text-sm">
        {data.summary_bullets?.map((b, i) => (
          <div key={i}>• {b}</div>
        ))}
      </div>
    </div>
  );
}