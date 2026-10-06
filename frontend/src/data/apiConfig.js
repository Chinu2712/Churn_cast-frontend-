/*
  apiConfig.js — single source of truth for "is a real backend connected yet?"

  Today there is no backend: every dataset is read from a static JSON file in
  frontend/public/data/ (see useDataset.js). When the Java + WEKA backend
  described in docs/api/openapi.yaml is ready, connecting it requires
  changing exactly ONE thing: set VITE_API_BASE_URL (see .env.example).

  Nothing else in the app needs to change — useDataset(), apiClient.js and
  the pages that call predictChurn()/predictRevenueForecast()/triggerModelRetrain()
  already know how to switch between "static JSON" and "live API" based on
  this file.
*/

// Trim a trailing slash so route concatenation never produces "//api/v1/...".
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() ?? "";
export const API_BASE_URL = rawBaseUrl.replace(/\/+$/, "");

// True once VITE_API_BASE_URL is set (e.g. http://localhost:8080) -- flips every
// dataset hook and prediction call from static JSON to real HTTP requests.
export const IS_LIVE_API = API_BASE_URL.length > 0;

export const API_VERSION = "v1";

/*
  Route map: dataset name (as already used by useDataset(name)) -> REST path
  on the future backend. Kept in one place so the contract documented in
  docs/api/openapi.yaml and the frontend fetch calls can never drift apart.
*/
export const DATASET_ROUTES = {
  customers: "/customers",
  monthly_revenue: "/revenue/monthly",
  revenue_history: "/revenue/history",
  cohort_retention: "/cohorts/retention",
  feature_contributions: "/explainability/feature-contributions",
  backtest_metrics: "/model/backtest-metrics",
  calibration: "/model/calibration",
  drift_metrics: "/model/drift-metrics",
  drift_distributions: "/model/drift-distributions",
  leakage_checklist: "/model/leakage-checklist",
  model_meta: "/model/meta",
};

export const PREDICTION_ROUTES = {
  churn: "/predictions/churn",
  revenueForecast: "/predictions/revenue-forecast",
  retrain: "/model/retrain",
};

export function apiUrl(path) {
  return `${API_BASE_URL}/api/${API_VERSION}${path}`;
}
