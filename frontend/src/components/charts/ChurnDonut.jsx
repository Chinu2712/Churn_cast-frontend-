import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const BUCKET_COLORS = { High: "var(--bad)", Medium: "var(--neutral)", Low: "var(--good)" };
const BUCKET_ORDER = ["High", "Medium", "Low"];

/** Donut chart of customer counts per risk bucket, with the total in the middle. */
export default function ChurnDonut({ customers }) {
  const counts = BUCKET_ORDER.map((bucket) => ({
    name: bucket,
    value: customers.filter((c) => c["Risk Bucket"] === bucket).length,
  }));
  const total = customers.length;

  return (
    <div style={{ position: "relative" }}>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={counts}
            dataKey="value"
            nameKey="name"
            innerRadius="60%"
            outerRadius="90%"
            paddingAngle={2}
            stroke="none"
          >
            {counts.map((entry) => (
              <Cell key={entry.name} fill={BUCKET_COLORS[entry.name]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value, name) => [`${value} customers`, name]}
            contentStyle={{ background: "var(--card-bg)", border: "1px solid var(--border)", fontSize: 12 }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div
        style={{
          position: "absolute", top: "40%", left: "50%", transform: "translate(-50%, -50%)",
          textAlign: "center", pointerEvents: "none",
        }}
      >
        <div style={{ fontWeight: 700, fontSize: 18 }}>{total}</div>
        <div style={{ fontSize: 10, color: "var(--text-light)" }}>customers</div>
      </div>
      <div className="legend">
        {counts.map((c) => (
          <span key={c.name}>
            <span className="dot" style={{ background: BUCKET_COLORS[c.name] }} />
            {c.name} {total ? Math.round((c.value / total) * 100) : 0}%
          </span>
        ))}
      </div>
    </div>
  );
}
