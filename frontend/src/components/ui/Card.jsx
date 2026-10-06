/*
  Card / Section — the two container primitives every visual sits in.

  <Card> is a plain bordered box (used for KPI tiles).
  <Section> additionally renders a title + divider, for the bigger
  chart/table containers (mirrors the "section()" helper from the earlier
  mockups, now as a real reusable component).
*/
export function Card({ children, className = "", style }) {
  return (
    <div className={`card ${className}`} style={style}>
      {children}
    </div>
  );
}

export function Section({ title, subtitle, children, className = "", style }) {
  return (
    <Card className={className} style={style}>
      <h3>
        {title}
        {subtitle ? <span className="card-subtitle"> {subtitle}</span> : null}
      </h3>
      {children}
    </Card>
  );
}
