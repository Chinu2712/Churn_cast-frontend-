/*
  apiClient.js — thin fetch wrapper for the future Java + WEKA backend.

  There is no backend yet, so every function here is written to be exercised
  end-to-end once one exists, without any other file changing:

    1. Static mode (today, default): VITE_API_BASE_URL is unset, IS_LIVE_API
       is false. Dataset reads go through useDataset()'s static JSON path;
       predictChurn()/predictRevenueForecast()/triggerModelRetrain() fall
       back to the existing client-side mock behavior so the UI keeps working.
    2. Live mode (future): set VITE_API_BASE_URL (see .env.example) to the
       Spring Boot server's origin. IS_LIVE_API flips to true, useDataset()
       starts fetching JSON from the real routes, and the prediction/retrain
       calls below POST to the real WEKA-backed endpoints documented in
       docs/api/openapi.yaml.

  Every request/response shape here matches that OpenAPI contract exactly --
  keep them in sync if either one changes.
*/
import { apiUrl, PREDICTION_ROUTES } from "./apiConfig";

const DEFAULT_TIMEOUT_MS = 10_000;

export class ApiError extends Error {
  constructor(message, { status, url, cause } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.url = url;
    this.cause = cause;
  }
}

async function request(path, { method = "GET", body, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  const url = apiUrl(path);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    if (!res.ok) {
      let detail;
      try {
        detail = await res.json();
      } catch {
        detail = await res.text().catch(() => undefined);
      }
      throw new ApiError(`${method} ${path} failed with ${res.status}`, { status: res.status, url, cause: detail });
    }

    if (res.status === 204) return null;
    return res.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(`${method} ${path} could not reach the backend at ${url}`, { url, cause: err });
  } finally {
    clearTimeout(timeout);
  }
}

export const apiGet = (path, options) => request(path, { ...options, method: "GET" });
export const apiPost = (path, body, options) => request(path, { ...options, method: "POST", body });

/*
  predictChurn — POST /api/v1/predictions/churn

  Backend contract (see docs/api/openapi.yaml -> ChurnPredictionRequest /
  ChurnPredictionResponse): send the customer's current feature snapshot plus
  the hypothetical usage_drop_percent from the Customer Risk Explorer's
  what-if slider, and the WEKA model returns a re-scored churn probability
  and predicted revenue impact -- replacing the linear client-side formula
  in utils/churnSimulation.js once a backend is connected.
*/
export function predictChurn({ customerId, usageDropPercent }) {
  return apiPost(PREDICTION_ROUTES.churn, {
    customer_id: customerId,
    usage_drop_percent: usageDropPercent,
  });
}

/*
  predictRevenueForecast — POST /api/v1/predictions/revenue-forecast

  Backend contract: request an updated next-month revenue forecast (point
  estimate + prediction interval) from the WEKA regression model, optionally
  scoped to a horizon in months. Used to refresh the Overview page's forecast
  KPI/chart on demand instead of only reading the precomputed monthly_revenue
  dataset.
*/
export function predictRevenueForecast({ horizonMonths = 1 } = {}) {
  return apiPost(PREDICTION_ROUTES.revenueForecast, { horizon_months: horizonMonths });
}

/*
  triggerModelRetrain — POST /api/v1/model/retrain

  Backend contract: kicks off an asynchronous WEKA retraining job (churn
  classifier + revenue regressor) and returns a job id/status immediately;
  the Model Diagnostics page polls or re-fetches model_meta afterwards.
*/
export function triggerModelRetrain() {
  return apiPost(PREDICTION_ROUTES.retrain, {});
}
