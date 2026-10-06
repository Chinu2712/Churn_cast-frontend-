/*
  Sparkline — a tiny, axis-free trend line for inline use in table rows.

  Deliberately plain SVG rather than a charting library: a sparkline is just
  "connect these points, scaled to fit a small box," and doing that by hand
  keeps the component a one-glance read for anyone reviewing the code.
*/
export default function Sparkline({ values, width = 90, height = 24, color = "var(--accent)" }) {
  if (!values || values.length < 2) return null;

  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const span = hi - lo || 1;

  const points = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = height - ((v - lo) / span) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polyline fill="none" stroke={color} strokeWidth="2" points={points} />
    </svg>
  );
}
