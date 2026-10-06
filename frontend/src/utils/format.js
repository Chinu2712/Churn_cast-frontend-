/*
  format.js — small, dependency-free number formatters.

  Centralizing these means every card/table renders numbers the same way
  (e.g. always 1 decimal place for percentages), and uses the browser's
  built-in Intl API instead of a formatting library.
*/

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const currencyCentsFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

export function formatCurrency(value, { cents = false } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return (cents ? currencyCentsFormatter : currencyFormatter).format(value);
}

export function formatPercent(value, { fromFraction = true, decimals = 1 } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const pct = fromFraction ? value * 100 : value;
  return `${pct.toFixed(decimals)}%`;
}

export function formatNumber(value, decimals = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("en-US", { maximumFractionDigits: decimals, minimumFractionDigits: decimals });
}

export function formatDate(isoString, { month = "short", day = "numeric", year = "numeric" } = {}) {
  if (!isoString) return "—";
  return new Date(isoString).toLocaleDateString("en-US", { month, day, year });
}

export function daysAgo(isoString) {
  if (!isoString) return "—";
  const diffMs = Date.now() - new Date(isoString).getTime();
  const days = Math.max(0, Math.round(diffMs / (1000 * 60 * 60 * 24)));
  if (days === 0) return "today";
  if (days === 1) return "1 day ago";
  return `${days} days ago`;
}

/** "High" / "Medium" / "Low" -> the CSS class suffix used by <Badge>. */
export function riskBucketClass(bucket) {
  return (bucket || "").toLowerCase();
}
