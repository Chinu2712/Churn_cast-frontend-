import { useEffect, useRef, useState } from "react";
import { IS_LIVE_API } from "./apiConfig";
import { predictChurn } from "./apiClient";
import { simulateChurnProbability, simulateRevenueImpact } from "../utils/churnSimulation";

/*
  useChurnPrediction — powers the "What-If: Usage Drop Simulation" panel on
  the Customer Risk Explorer page.

  This is the piece that makes sure a connected WEKA backend actually shows
  up in the UI instead of just being reachable in theory:

  - No backend connected (VITE_API_BASE_URL unset, IS_LIVE_API === false):
    behaves exactly as before -- an instant, synchronous client-side formula
    (utils/churnSimulation.js), source = "simulated".

  - Backend connected (IS_LIVE_API === true): every slider move calls
    POST /api/v1/predictions/churn (see docs/api/openapi.yaml) and renders
    whatever churn probability / revenue impact the WEKA model returns,
    source = "live". Requests are debounced so dragging the slider doesn't
    flood the backend, and the in-flight request is aborted/ignored if the
    slider moves again or the selected customer changes before it resolves.

  - Backend connected but unreachable for this request (network error,
    5xx, timeout): falls back to the same client-side formula so the panel
    never goes blank, source = "simulated-fallback", and the error is
    returned so the UI can surface a small warning.
*/
export function useChurnPrediction({ customer, usageDropPercent }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (!customer) {
      setResult(null);
      setError(null);
      setLoading(false);
      return;
    }

    const localFallback = () => {
      const simProb = simulateChurnProbability(customer.churn_probability, usageDropPercent);
      const simImpact = simulateRevenueImpact(customer.monthly_revenue, customer.churn_probability, simProb);
      return { simProb, simImpact };
    };

    if (!IS_LIVE_API) {
      setResult({ ...localFallback(), source: "simulated" });
      setError(null);
      setLoading(false);
      return;
    }

    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);

    const debounce = setTimeout(() => {
      predictChurn({ customerId: customer.customer_id, usageDropPercent })
        .then((response) => {
          if (requestIdRef.current !== requestId) return; // stale response, ignore
          setResult({
            simProb: response.churn_probability,
            simImpact: response.predicted_revenue_impact,
            source: "live",
          });
          setLoading(false);
        })
        .catch((err) => {
          if (requestIdRef.current !== requestId) return;
          setResult({ ...localFallback(), source: "simulated-fallback" });
          setError(err);
          setLoading(false);
        });
    }, 250);

    return () => clearTimeout(debounce);
  }, [customer, usageDropPercent]);

  return { result, loading, error };
}
