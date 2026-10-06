import { useMemo } from "react";

/*
  CohortHeatmap — retention % by signup cohort (rows) x months since signup
  (columns). Power BI would call this a "matrix with conditional
  formatting"; here it's a plain grid of colored <div>s, which is simpler to
  build and just as readable.
*/
export default function CohortHeatmap({ rows }) {
  const { cohorts, maxMonth } = useMemo(() => {
    const bySignup = new Map();
    let maxMonth = 0;
    for (const r of rows) {
      if (!bySignup.has(r.signup_month)) bySignup.set(r.signup_month, { order: r.cohort_order, cells: new Map() });
      bySignup.get(r.signup_month).cells.set(r.months_since_signup, r);
      maxMonth = Math.max(maxMonth, r.months_since_signup);
    }
    const cohorts = [...bySignup.entries()]
      .sort((a, b) => a[1].order - b[1].order)
      .map(([signup_month, info]) => ({ signup_month, cells: info.cells }));
    return { cohorts, maxMonth };
  }, [rows]);

  return (
    <div style={{ overflowX: "auto" }}>
      <div style={{ display: "grid", gridTemplateColumns: `90px repeat(${maxMonth + 1}, 1fr)`, gap: 3, minWidth: 560 }}>
        <div />
        {Array.from({ length: maxMonth + 1 }, (_, i) => (
          <div key={i} style={{ fontSize: 9, color: "var(--text-light)", textAlign: "center" }}>{i}</div>
        ))}
        {cohorts.map((cohort) => (
          <RowCells key={cohort.signup_month} cohort={cohort} maxMonth={maxMonth} />
        ))}
      </div>
      <p className="note-text" style={{ marginTop: 10 }}>
        Each row = signup cohort, each column = months since signup. Darker = higher retention.
        The gold-outlined cell per row is the forecasted next-month retention.
      </p>
    </div>
  );
}

function RowCells({ cohort, maxMonth }) {
  return (
    <>
      <div style={{ fontSize: 10, color: "var(--text-light)", display: "flex", alignItems: "center" }}>
        {cohort.signup_month}
      </div>
      {Array.from({ length: maxMonth + 1 }, (_, month) => {
        const cell = cohort.cells.get(month);
        if (!cell) return <div key={month} />;
        const pct = cell.retention_rate / 100;
        const bg = `rgba(47, 107, 138, ${0.12 + pct * 0.75})`;
        return (
          <div
            key={month}
            title={`${cohort.signup_month}, month ${month}: ${cell.retention_rate.toFixed(1)}% retained`}
            style={{
              background: bg,
              height: 22,
              borderRadius: 3,
              outline: cell.is_forecast ? "2px solid var(--neutral)" : "none",
            }}
          />
        );
      })}
    </>
  );
}
