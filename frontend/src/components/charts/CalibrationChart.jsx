import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import { formatPercent } from "../../utils/format";

/*
  CalibrationChart — reliability curve: for each predicted-probability
  decile, how close is the average predicted probability to what actually
  happened? A well-calibrated model keeps the two lines close together.
*/
export default function CalibrationChart({ rows }) {
  const sorted = [...rows].sort((a, b) => a.bucket_order - b.bucket_order);
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={sorted} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="bucket_label" fontSize={10} stroke="var(--text-light)" />
        <YAxis tickFormatter={(v) => formatPercent(v, { fromFraction: false })} fontSize={11} stroke="var(--text-light)" />
        <Tooltip
          formatter={(value) => formatPercent(value, { fromFraction: false })}
          contentStyle={{ background: "var(--card-bg)", border: "1px solid var(--border)", fontSize: 12 }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line dataKey={(d) => d.predicted_avg * 100} name="Predicted avg." stroke="var(--accent)" strokeWidth={2.5} dot />
        <Line dataKey={(d) => d.actual_rate * 100} name="Actual churn rate" stroke="var(--neutral)" strokeWidth={2.5} dot strokeDasharray="5 4" />
      </LineChart>
    </ResponsiveContainer>
  );
}
