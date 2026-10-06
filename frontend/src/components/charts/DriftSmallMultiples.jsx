import { ResponsiveContainer, BarChart, Bar, XAxis, Tooltip } from "recharts";

/*
  DriftSmallMultiples — one mini histogram per monitored feature, each
  comparing the "Baseline" vs "Recent" signup distribution. A visually wide
  gap between the two bars for a bucket is the human-readable version of
  the KS-statistic drift flag shown in the table next to this component.
*/
export default function DriftSmallMultiples({ rows, driftFlags }) {
  const featureNames = [...new Set(rows.map((r) => r.feature_name))];

  return (
    <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
      {featureNames.map((feature) => {
        const featureRows = rows.filter((r) => r.feature_name === feature);
        const byBucket = new Map();
        for (const r of featureRows) {
          if (!byBucket.has(r.bucket_order)) byBucket.set(r.bucket_order, { bucket_label: r.bucket_label });
          byBucket.get(r.bucket_order)[r.period] = r.proportion * 100;
        }
        const chartData = [...byBucket.values()].sort((a, b) => a.bucket_label.localeCompare(b.bucket_label));
        const flagged = driftFlags?.find((d) => d.feature_name === feature)?.drift_flag;

        return (
          <div key={feature}>
            <div style={{ fontSize: 11, fontWeight: 600, marginBottom: 4, display: "flex", justifyContent: "space-between" }}>
              <span>{feature}</span>
              {flagged ? <span style={{ color: "var(--bad)" }}>drift flagged</span> : <span style={{ color: "var(--good)" }}>stable</span>}
            </div>
            <ResponsiveContainer width="100%" height={110}>
              <BarChart data={chartData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                <XAxis dataKey="bucket_label" fontSize={8} stroke="var(--text-light)" interval={1} />
                <Tooltip
                  formatter={(v) => `${v.toFixed(1)}%`}
                  contentStyle={{ background: "var(--card-bg)", border: "1px solid var(--border)", fontSize: 11 }}
                />
                <Bar dataKey="Baseline" fill="var(--accent-light)" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Recent" fill={flagged ? "var(--bad)" : "var(--accent)"} radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      })}
    </div>
  );
}
