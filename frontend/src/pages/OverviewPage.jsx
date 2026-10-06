import { useMemo } from "react";
import PageLayout from "../components/layout/PageLayout";
import TopBar from "../components/layout/TopBar";
import { Section } from "../components/ui/Card";
import KpiCard from "../components/ui/KpiCard";
import Badge from "../components/ui/Badge";
import DataState from "../components/ui/DataState";
import Sparkline from "../components/ui/Sparkline";
import ForecastChart from "../components/charts/ForecastChart";
import ChurnDonut from "../components/charts/ChurnDonut";
import CohortHeatmap from "../components/charts/CohortHeatmap";
import { useDataset } from "../data/useDataset";
import { useCustomers } from "../data/useCustomers";
import { useRevenueForecast } from "../data/useRevenueForecast";
import { IS_LIVE_API } from "../data/apiConfig";
import { formatCurrency, formatPercent, formatDate, daysAgo } from "../utils/format";

export default function OverviewPage() {
  const monthlyRevenue = useDataset("monthly_revenue");
  const customers = useCustomers();
  const backtestMetrics = useDataset("backtest_metrics");
  const modelMeta = useDataset("model_meta");
  const cohortRetention = useDataset("cohort_retention");

  const ready = monthlyRevenue.data && customers.data && backtestMetrics.data && modelMeta.data && cohortRetention.data;
  const loading = !ready && ![monthlyRevenue, customers, backtestMetrics, modelMeta, cohortRetention].some((d) => d.error);
  const error = [monthlyRevenue, customers, backtestMetrics, modelMeta, cohortRetention].find((d) => d.error)?.error;

  // Defaults to the static monthly_revenue.json rows; once a backend is
  // connected, clicking "Refresh forecast" replaces the forecast month(s)
  // with a live WEKA prediction and the chart/KPIs below update immediately.
  const forecast = useRevenueForecast(monthlyRevenue.data);

  const kpis = useMemo(() => {
    if (!ready) return null;

    const rows = forecast.rows ?? monthlyRevenue.data;
    const forecastRow = rows.find((r) => r.is_forecast_month === 1);
    const lastActualRow = [...rows].reverse().find((r) => r.actual_revenue != null);
    const mapeMetric = backtestMetrics.data.find((m) => m.metric_name === "Revenue MAPE");
    const mapeTrendValues = rows.map((r) => r.mape_trend).filter((v) => v != null);

    const revenueAtRisk = customers.data.reduce((sum, c) => sum + (c.predicted_revenue_loss || 0), 0);
    const highRiskCount = customers.data.filter((c) => c["Risk Bucket"] === "High").length;
    const pctHighRisk = highRiskCount / customers.data.length;

    const meta = modelMeta.data[0];
    const aucMetric = backtestMetrics.data.find((m) => m.metric_name === "Churn AUC");

    const topAlerts = [...customers.data]
      .sort((a, b) => b.churn_probability - a.churn_probability)
      .slice(0, 6);

    return { forecastRow, lastActualRow, mapeMetric, mapeTrendValues, revenueAtRisk, pctHighRisk, meta, aucMetric, topAlerts };
  }, [ready, forecast.rows, monthlyRevenue.data, customers.data, backtestMetrics.data, modelMeta.data]);

  return (
    <PageLayout>
      <TopBar title="ChurnCast — Overview" />
      <DataState loading={loading} error={error}>
        {ready && (
          <>
            {/* KPI row */}
            <div className="grid" style={{ gridTemplateColumns: "repeat(3, 1fr) 1.2fr 1.8fr", marginBottom: 16 }}>
              <KpiCard label="Next Month Revenue (Forecast)" value={formatCurrency(kpis.forecastRow?.forecast_revenue)} />
              <KpiCard label="Actual Revenue (MTD)" value={formatCurrency(kpis.lastActualRow?.actual_revenue)} />
              <KpiCard label="Forecast Error (MAPE)" value={kpis.mapeMetric?.metric_display ?? "—"} />
              <Section title="MAPE Trend">
                <Sparkline values={kpis.mapeTrendValues} width={110} height={42} color="var(--neutral)" />
              </Section>
              <Section title="Accuracy Note" subtitle="(built from data, not hardcoded)">
                <p className="note-text">
                  "Model trained on data from {formatDate(kpis.meta.holdout_start, { day: undefined })} to{" "}
                  {formatDate(kpis.meta.holdout_end, { day: undefined })}. Holdout MAPE ={" "}
                  {formatPercent(kpis.mapeMetric?.metric_value, { fromFraction: false })}, AUC ={" "}
                  {kpis.aucMetric?.metric_value?.toFixed(2)}. Use predictions as decision support; validate before
                  high-cost actions."
                </p>
              </Section>
            </div>

            {/* Forecast chart + churn donut + risk KPIs */}
            <div className="grid" style={{ gridTemplateColumns: "3fr 1.2fr 0.9fr", marginBottom: 16, alignItems: "stretch" }}>
              <Section
                title="Forecast vs Actual Revenue"
                subtitle={
                  IS_LIVE_API ? (
                    <button
                      className="btn"
                      style={{ fontSize: 11, padding: "2px 8px" }}
                      onClick={() => forecast.refresh(1)}
                      disabled={forecast.loading}
                    >
                      {forecast.loading ? "Refreshing…" : forecast.source === "live" ? "↻ Refresh WEKA forecast" : "Get live WEKA forecast"}
                    </button>
                  ) : undefined
                }
              >
                <ForecastChart rows={forecast.rows ?? monthlyRevenue.data} />
                <div className="legend">
                  <span><span className="dot" style={{ background: "var(--accent)" }} /> Actual / Forecast line</span>
                  <span><span className="dot" style={{ background: "var(--accent-light)" }} /> Prediction interval (shaded)</span>
                </div>
                {forecast.source === "live" && (
                  <p className="note-text" style={{ marginTop: 6, color: "var(--good)" }}>
                    ● Forecast line/band above reflects the latest live WEKA prediction.
                  </p>
                )}
                {forecast.error && (
                  <p className="note-text" style={{ marginTop: 6 }}>
                    Could not refresh from the backend ({forecast.error.message}); showing last known forecast.
                  </p>
                )}
              </Section>
              <Section title="Churn Risk Summary">
                <ChurnDonut customers={customers.data} />
              </Section>
              <div className="grid" style={{ gridTemplateColumns: "1fr" }}>
                <KpiCard label="Revenue at Risk" value={formatCurrency(kpis.revenueAtRisk)} tone="bad" />
                <KpiCard label="% High Risk Customers" value={formatPercent(kpis.pctHighRisk)} tone="bad" />
              </div>
            </div>

            {/* Cohort retention + alerts panel */}
            <div className="grid" style={{ gridTemplateColumns: "1.1fr 1fr" }}>
              <Section title="Cohort Retention" subtitle="(signup month × months since signup)">
                <CohortHeatmap rows={cohortRetention.data} />
              </Section>
              <Section title="Actionable Alerts — Top Customers to Contact">
                <table>
                  <thead>
                    <tr>
                      <th>Customer</th><th>Risk</th><th>Churn %</th><th>Rev. at risk</th><th>Last active</th>
                    </tr>
                  </thead>
                  <tbody>
                    {kpis.topAlerts.map((c) => (
                      <tr key={c.customer_id}>
                        <td>{c.customer_name}</td>
                        <td><Badge>{c["Risk Bucket"]}</Badge></td>
                        <td>{formatPercent(c.churn_probability)}</td>
                        <td>{formatCurrency(c.predicted_revenue_loss, { cents: true })}</td>
                        <td>{daysAgo(c.last_active_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="actions">
                  <button className="btn" onClick={() => exportCsv(kpis.topAlerts)}>Export list (CSV)</button>
                  <button className="btn" onClick={() => alert("Would open the CRM record for the selected customer in a real deployment.")}>
                    Open in CRM
                  </button>
                </div>
              </Section>
            </div>
          </>
        )}
      </DataState>
    </PageLayout>
  );
}

/** Minimal client-side CSV export -- no library needed for 6 columns. */
function exportCsv(rows) {
  const headers = ["customer_id", "customer_name", "Risk Bucket", "churn_probability", "predicted_revenue_loss", "last_active_date"];
  const csv = [headers.join(",")]
    .concat(rows.map((r) => headers.map((h) => JSON.stringify(r[h] ?? "")).join(",")))
    .join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "churncast-at-risk-customers.csv";
  a.click();
  URL.revokeObjectURL(url);
}
