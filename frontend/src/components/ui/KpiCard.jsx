import { Card } from "./Card";

/** A single number-first metric tile, e.g. "Next Month Revenue: $23,100". */
export default function KpiCard({ label, value, tone = "accent" }) {
  return (
    <Card>
      <h3>{label}</h3>
      <div className={`kpi-value ${tone === "accent" ? "" : tone}`}>{value}</div>
    </Card>
  );
}
