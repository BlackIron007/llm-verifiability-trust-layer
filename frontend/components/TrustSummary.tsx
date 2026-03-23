export default function TrustSummary({ data }) {
  const score = data.overall_trust_score;
  const scorePercentage = (score * 100).toFixed(0);

  let statusIcon = "🔴";
  let statusText = "Low Trust";
  let statusColor = "text-red-500";

  if (score >= 0.7) {
    statusIcon = "🟢";
    statusText = "High Trust";
    statusColor = "text-green-600";
  } else if (score >= 0.4) {
    statusIcon = "🟡";
    statusText = "Medium Trust";
    statusColor = "text-amber-500";
  }

  return (
    <div className="border border-border rounded-lg p-8 bg-surface shadow-sm">
      <h2 className="text-xl font-light text-text mb-6">Trust Summary</h2>

      <div className="flex items-end gap-4 mb-6">
        <div className="text-5xl font-light text-text">{scorePercentage}%</div>
        <div className={`text-lg font-medium flex items-center gap-2 ${statusColor} mb-1`}>
          <span>{statusIcon}</span> {statusText}
        </div>
      </div>

      <div className="space-y-3 text-base leading-relaxed text-text font-light">
        {data.summary_bullets?.map((b, i) => (
          <div key={i} className="flex items-start gap-3"><span className="text-accent">•</span> <span>{b}</span></div>
        ))}
      </div>
    </div>
  );
}