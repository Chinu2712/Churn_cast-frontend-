import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import PageLayout from "../components/layout/PageLayout";
import TopBar from "../components/layout/TopBar";
import { Section } from "../components/ui/Card";
import KpiCard from "../components/ui/KpiCard";
import Badge from "../components/ui/Badge";
import DataState from "../components/ui/DataState";
import Sparkline from "../components/ui/Sparkline";
import FeatureBarChart from "../components/charts/FeatureBarChart";
import { useDataset } from "../data/useDataset";
import { useCustomers } from "../data/useCustomers";
import { useChurnPrediction } from "../data/usePrediction";
import { formatCurrency, formatPercent, daysAgo } from "../utils/format";

const FILTER_FIELDS = [
  { key: "contract_type", label: "Contract Type" },
  { key: "region", label: "Region" },
  { key: "plan", label: "Plan" },
  { key: "Tenure Bucket", label: "Tenure Bucket" },
];

export default function CustomerRiskExplorerPage() {
  const customers = useCustomers();
  const featureContributions = useDataset("feature_contributions");
  const revenueHistory = useDataset("revenue_history");

  const ready = customers.data && featureContributions.data && revenueHistory.data;
  const loading = !ready && ![customers, featureContributions, revenueHistory].some((d) => d.error);
  const error = [customers, featureContributions, revenueHistory].find((d) => d.error)?.error;

  const [filters, setFilters] = useState({});
  const [sortKey, setSortKey] = useState("churn_probability");
  const [sortDesc, setSortDesc] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [usageDrop, setUsageDrop] = useState(0);

  const filterOptions = useMemo(() => {
    if (!ready) return {};
    const options = {};
    for (const field of FILTER_FIELDS) {
      options[field.key] = [...new Set(customers.data.map((c) => c[field.key]))].sort();
    }
    return options;
  }, [ready, customers.data]);

  const revenueByCustomer = useMemo(() => {
    if (!ready) return new Map();
    const map = new Map();
    for (const row of revenueHistory.data) {
      if (!map.has(row.customer_id)) map.set(row.customer_id, []);
      map.get(row.customer_id).push(row.revenue);
    }
    return map;
  }, [ready, revenueHistory.data]);

  const filteredSortedCustomers = useMemo(() => {
    if (!ready) return [];
    let rows = customers.data.filter((c) =>
      FILTER_FIELDS.every((f) => !filters[f.key] || c[f.key] === filters[f.key])
    );
    rows = [...rows].sort((a, b) => {
      const diff = (a[sortKey] ?? 0) > (b[sortKey] ?? 0) ? 1 : -1;
      return sortDesc ? -diff : diff;
    });
    return rows;
  }, [ready, customers.data, filters, sortKey, sortDesc]);

  const selectedCustomer = useMemo(
    () => (ready ? customers.data.find((c) => c.customer_id === selectedId) : null),
    [ready, customers.data, selectedId]
  );

  const selectedContributions = useMemo(() => {
    if (!ready || !selectedId) return [];
    return featureContributions.data
      .filter((f) => f.customer_id === selectedId)
      .sort((a, b) => a.rank - b.rank);
  }, [ready, featureContributions.data, selectedId]);

  // Returns a client-side simulation today; automatically switches to a real
  // POST /api/v1/predictions/churn call against the WEKA model once a
  // backend is connected (see data/usePrediction.js).
  const { result: simulation, loading: simulationLoading, error: simulationError } = useChurnPrediction({
    customer: selectedCustomer,
    usageDropPercent: usageDrop,
  });

  function toggleSort(key) {
    if (sortKey === key) setSortDesc((d) => !d);
    else {
      setSortKey(key);
      setSortDesc(true);
    }
  }

  return (
    <PageLayout>
      <TopBar title="Customer Risk Explorer" />
      <DataState loading={loading} error={error}>
        {ready && (
          <>
            <div className="slicers">
              {FILTER_FIELDS.map((f) => (
                <div className="slicer" key={f.key}>
                  <h4>{f.label}</h4>
                  <select
                    value={filters[f.key] ?? ""}
                    onChange={(e) => setFilters((prev) => ({ ...prev, [f.key]: e.target.value || undefined }))}
                  >
                    <option value="">All</option>
                    {filterOptions[f.key].map((opt) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            <div className="grid" style={{ gridTemplateColumns: "1.6fr 1fr", alignItems: "start" }}>
              <Section title={`Customer List — ${filteredSortedCustomers.length} customers`} subtitle="(click a row to explore; drillthrough for full detail)">
                <table>
                  <thead>
                    <tr>
                      <th onClick={() => toggleSort("customer_name")}>Customer</th>
                      <th onClick={() => toggleSort("churn_probability")}>Risk</th>
                      <th onClick={() => toggleSort("churn_probability")}>Churn %</th>
                      <th onClick={() => toggleSort("tenure_months")}>Tenure</th>
                      <th onClick={() => toggleSort("last_active_date")}>Last Active</th>
                      <th onClick={() => toggleSort("predicted_revenue_loss")}>Predicted Loss</th>
                      <th>Revenue trend</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSortedCustomers.slice(0, 50).map((c) => (
                      <tr
                        key={c.customer_id}
                        className="clickable"
                        onClick={() => { setSelectedId(c.customer_id); setUsageDrop(0); }}
                        style={{ background: c.customer_id === selectedId ? "var(--bg)" : undefined }}
                      >
                        <td>{c.customer_name}</td>
                        <td><Badge>{c["Risk Bucket"]}</Badge></td>
                        <td>{formatPercent(c.churn_probability)}</td>
                        <td>{c.tenure_months} mo</td>
                        <td>{daysAgo(c.last_active_date)}</td>
                        <td>{formatCurrency(c.predicted_revenue_loss, { cents: true })}</td>
                        <td><Sparkline values={(revenueByCustomer.get(c.customer_id) || []).slice(-6)} /></td>
                        <td>
                          <Link to={`/customer/${c.customer_id}`} onClick={(e) => e.stopPropagation()} title="Open full detail page">
                            &rarr;
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredSortedCustomers.length > 50 && (
                  <p className="note-text">Showing top 50 of {filteredSortedCustomers.length} matching customers.</p>
                )}
              </Section>

              <div className="grid" style={{ gridTemplateColumns: "1fr" }}>
                <Section title="Explainability" subtitle="— top 5 feature contributions (selected customer)">
                  {selectedCustomer ? (
                    <>
                      <p className="note-text" style={{ marginBottom: 10 }}>
                        Selected: <strong style={{ color: "var(--text)" }}>{selectedCustomer.customer_name}</strong>
                      </p>
                      <FeatureBarChart contributions={selectedContributions} />
                    </>
                  ) : (
                    <p className="note-text">Click a customer row to see what is driving their churn score.</p>
                  )}
                </Section>

                <Section title="What-If: Usage Drop Simulation">
                  <p className="note-text" style={{ marginBottom: 12 }}>
                    Adjust the slider to see how a further usage drop would change the selected customer's churn
                    risk. {" "}
                    <PredictionSourceNote source={simulation?.source} loading={simulationLoading} error={simulationError} />
                  </p>
                  <div className="slider-row">
                    <input
                      type="range" min={0} max={100} step={5} value={usageDrop}
                      disabled={!selectedCustomer}
                      onChange={(e) => setUsageDrop(Number(e.target.value))}
                      aria-label="Usage drop percentage"
                    />
                    <span className="slider-value">{usageDrop}%</span>
                  </div>
                  <div className="kpi-pair">
                    <KpiCard
                      label={simulation?.source === "live" ? "Predicted Churn Probability (WEKA)" : "Simulated Churn Probability"}
                      value={simulation ? formatPercent(simulation.simProb) : "—"}
                    />
                    <KpiCard
                      label={simulation?.source === "live" ? "Predicted Revenue Impact (WEKA)" : "Simulated Revenue Impact"}
                      value={simulation ? `${simulation.simImpact >= 0 ? "+" : ""}${formatCurrency(simulation.simImpact, { cents: true })}` : "—"}
                      tone={simulation && simulation.simImpact < 0 ? "bad" : "accent"}
                    />
                  </div>
                </Section>
              </div>
            </div>
          </>
        )}
      </DataState>
    </PageLayout>
  );
}

/*
  PredictionSourceNote — makes it obvious in the UI whether the churn number
  above came from the real WEKA backend or the client-side fallback formula,
  so connecting the backend is visibly verifiable during a demo.
*/
function PredictionSourceNote({ source, loading, error }) {
  if (loading) return <span style={{ color: "var(--text-light)" }}>Scoring with WEKA backend…</span>;
  if (source === "live") return <span style={{ color: "var(--good)" }}>● Live prediction from WEKA backend</span>;
  if (source === "simulated-fallback") {
    return (
      <span style={{ color: "var(--neutral)" }}>
        ● Backend unreachable — showing client-side estimate{error ? ` (${error.message})` : ""}
      </span>
    );
  }
  return <span>(client-side simulation — no server round-trip)</span>;
}
