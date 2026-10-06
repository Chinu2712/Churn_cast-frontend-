import { useCallback, useMemo, useState } from "react";
import { IS_LIVE_API } from "./apiConfig";
import { predictRevenueForecast } from "./apiClient";

/*
  useRevenueForecast — makes the Overview page's forecast chart/KPIs show a
  live WEKA prediction instead of only the precomputed monthly_revenue.json
  snapshot, once a backend is connected.

  Usage: const { rows, refresh, loading, error, source } = useRevenueForecast(monthlyRevenue.data)
  - `rows` is what ForecastChart/KpiCards should render: the base dataset,
    with any months returned by a live refresh() merged in/overridden.
  - refresh() calls POST /api/v1/predictions/revenue-forecast (see
    docs/api/openapi.yaml) and merges the response by month. No-op (and
    clearly a no-op, via IS_LIVE_API) until a backend is connected.
*/
export function useRevenueForecast(baseRows) {
  const [liveForecasts, setLiveForecasts] = useState(null); // Map<month, row> | null
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback((horizonMonths = 1) => {
    if (!IS_LIVE_API) return;
    setLoading(true);
    setError(null);
    predictRevenueForecast({ horizonMonths })
      .then((response) => {
        const byMonth = new Map((response.forecasts ?? []).map((row) => [row.month, row]));
        setLiveForecasts(byMonth);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });
  }, []);

  const rows = useMemo(() => {
    if (!baseRows) return baseRows;
    if (!liveForecasts || liveForecasts.size === 0) return baseRows;

    const merged = baseRows.map((row) => {
      const liveRow = liveForecasts.get(row.month);
      return liveRow ? { ...row, ...liveRow, is_forecast_month: 1 } : row;
    });

    // Any forecasted months beyond the existing dataset (e.g. a multi-month
    // horizon request) get appended as new rows so the chart's x-axis grows.
    const existingMonths = new Set(baseRows.map((r) => r.month));
    const extraRows = [...liveForecasts.values()].filter((r) => !existingMonths.has(r.month));
    return [...merged, ...extraRows.map((r) => ({ ...r, is_forecast_month: 1 }))].sort((a, b) =>
      a.month < b.month ? -1 : a.month > b.month ? 1 : 0
    );
  }, [baseRows, liveForecasts]);

  return {
    rows,
    refresh,
    loading,
    error,
    source: liveForecasts ? "live" : "static",
  };
}
