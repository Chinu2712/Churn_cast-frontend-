import { useState } from "react";
import PageLayout from "../components/layout/PageLayout";
import TopBar from "../components/layout/TopBar";
import { Section } from "../components/ui/Card";
import KpiCard from "../components/ui/KpiCard";
import DataState from "../components/ui/DataState";
import CalibrationChart from "../components/charts/CalibrationChart";
import DriftSmallMultiples from "../components/charts/DriftSmallMultiples";
import { useDataset } from "../data/useDataset";
import { IS_LIVE_API } from "../data/apiConfig";
import { triggerModelRetrain } from "../data/apiClient";
import { formatDate, formatPercent } from "../utils/format";

export default function ModelDiagnosticsPage() {
  const backtestMetrics = useDataset("backtest_metrics");
  const calibration = useDataset("calibration");
  const driftMetrics = useDataset("drift_metrics");
  const driftDistributions = useDataset("drift_distributions");
  const leakageChecklist = useDataset("leakage_checklist");
  const modelMeta = useDataset("model_meta");

  const allDatasets = [backtestMetrics, calibration, driftMetrics, driftDistributions, leakageChecklist, modelMeta];
  const ready = allDatasets.every((d) => d.data);
  const loading = !ready && !allDatasets.some((d) => d.error);
  const error = allDatasets.find((d) => d.error)?.error;

  const [retraining, setRetraining] = useState(false);
  const [retrainNote, setRetrainNote] = useState(null);

  function refetchDiagnostics() {
    // Pulls fresh numbers into every chart on this page (backtest metrics,
    // calibration, drift, model_meta) once the backend reports retraining
    // is done -- so the newly retrained WEKA model's accuracy is visible
    // here without a manual page reload.
    allDatasets.forEach((d) => d.refetch());
  }

  function handleRetrain() {
    setRetraining(true);
    setRetrainNote(null);

    if (!IS_LIVE_API) {
      // No backend connected yet: keep the original mocked behavior so the
      // button still demos something meaningful.
      setTimeout(() => {
        setRetraining(false);
        alert("Retraining pipeline triggered (mocked). Connect the backend (VITE_API_BASE_URL) to call the real WEKA retrain job.");
      }, 1200);
      return;
    }

    triggerModelRetrain()
      .then((response) => {
        setRetraining(false);
        setRetrainNote({ tone: "good", text: `Retrain job ${response.job_id ?? ""} ${response.status ?? "started"}.` });
        // The WEKA retrain job is asynchronous server-side (see
        // docs/api/openapi.yaml -> RetrainResponse); a production UI would
        // poll response.status_url until status === "completed" before
        // refetching. Here we refetch immediately so a fast/synchronous
        // backend implementation is reflected right away, and this is also
        // the exact call a polling loop would make once the job finishes.
        refetchDiagnostics();
      })
      .catch((err) => {
        setRetraining(false);
        setRetrainNote({ tone: "bad", text: `Retrain request failed: ${err.message}` });
      });
  }

  return (
    <PageLayout>
      <TopBar title="Model Diagnostics & Monitoring" />
      <DataState loading={loading} error={error}>
        {ready && (
          <>
            <div className="grid" style={{ gridTemplateColumns: "2fr 1fr 1fr 1.2fr", marginBottom: 16, alignItems: "stretch" }}>
              <Section title="Accuracy Note">
                <AccuracyNote modelMeta={modelMeta.data[0]} backtestMetrics={backtestMetrics.data} />
              </Section>
              <KpiCard label="Last Trained" value={formatDate(modelMeta.data[0].last_trained_date)} />
              <KpiCard label="Next Scheduled Retrain" value={formatDate(modelMeta.data[0].next_scheduled_retrain)} />
              <Section title="Retraining">
                <button className="btn" onClick={handleRetrain} disabled={retraining} style={{ width: "100%" }}>
                  {retraining ? "Triggering…" : IS_LIVE_API ? "Retrain Model (WEKA backend)" : "Retrain Model (Fabric pipeline)"}
                </button>
                {retrainNote && (
                  <p className="note-text" style={{ marginTop: 8, color: retrainNote.tone === "good" ? "var(--good)" : "var(--bad)" }}>
                    {retrainNote.text}
                  </p>
                )}
              </Section>
            </div>

            <div className="grid" style={{ gridTemplateColumns: "1fr 1.1fr", marginBottom: 16, alignItems: "start" }}>
              <Section title="Backtest Metrics" subtitle={`(holdout, n=${modelMeta.data[0].sample_size})`}>
                <table>
                  <thead><tr><th>Metric</th><th>Value</th><th>Type</th></tr></thead>
                  <tbody>
                    {backtestMetrics.data.map((m) => (
                      <tr key={m.metric_name}>
                        <td>{m.metric_name}</td>
                        <td style={{ fontWeight: 700 }}>{m.metric_display}</td>
                        <td>{m.metric_type}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Section>
              <Section title="Calibration Plot" subtitle="(predicted vs. actual churn rate per decile)">
                <CalibrationChart rows={calibration.data} />
              </Section>
            </div>

            <div className="grid" style={{ gridTemplateColumns: "1fr", marginBottom: 16 }}>
              <Section title="Drift Monitoring" subtitle="— baseline (older signups) vs. recent signups">
                <DriftSmallMultiples rows={driftDistributions.data} driftFlags={driftMetrics.data} />
              </Section>
            </div>

            <div className="grid" style={{ gridTemplateColumns: "1fr" }}>
              <Section title="Data Leakage Checklist">
                <table>
                  <thead>
                    <tr><th>Feature</th><th>Correlation with label</th><th>Flag</th><th>Note</th></tr>
                  </thead>
                  <tbody>
                    {leakageChecklist.data.map((row) => (
                      <tr key={row.feature_name}>
                        <td>{row.feature_name}</td>
                        <td>{row.correlation_with_label.toFixed(3)}</td>
                        <td>
                          {row.leakage_flag ? (
                            <span className="badge high">Flagged</span>
                          ) : (
                            <span className="badge low">OK</span>
                          )}
                        </td>
                        <td style={{ color: "var(--text-light)" }}>{row.note}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Section>
            </div>
          </>
        )}
      </DataState>
    </PageLayout>
  );
}

function AccuracyNote({ modelMeta, backtestMetrics }) {
  const mape = backtestMetrics.find((m) => m.metric_name === "Revenue MAPE");
  const auc = backtestMetrics.find((m) => m.metric_name === "Churn AUC");
  return (
    <p className="note-text">
      "Model trained on data from {formatDate(modelMeta.holdout_start, { day: undefined })} to{" "}
      {formatDate(modelMeta.holdout_end, { day: undefined })}. Holdout MAPE ={" "}
      {formatPercent(mape?.metric_value, { fromFraction: false })}, AUC = {auc?.metric_value?.toFixed(2)}.
      Sample size = {modelMeta.sample_size} customers. Use predictions as decision support; validate before
      high-cost actions."
    </p>
  );
}
