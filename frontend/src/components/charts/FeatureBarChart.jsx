/*
  FeatureBarChart — horizontal bars for the top-5 feature contributions of
  a selected customer. Plain divs (not Recharts) because the bars are
  simple proportional widths and this keeps it trivially explainable.
*/
export default function FeatureBarChart({ contributions }) {
  if (!contributions || contributions.length === 0) {
    return <p className="note-text">Select a customer row to see their top feature contributions.</p>;
  }
  const maxAbs = Math.max(...contributions.map((f) => Math.abs(f.contribution)), 0.0001);

  return (
    <div>
      {contributions.map((f) => {
        const widthPct = (Math.abs(f.contribution) / maxAbs) * 100;
        const color = f.contribution >= 0 ? "var(--bad)" : "var(--good)";
        return (
          <div className="bar-row" key={f.feature_name}>
            <div className="bar-label">{f.feature_name}</div>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${widthPct}%`, background: color }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
