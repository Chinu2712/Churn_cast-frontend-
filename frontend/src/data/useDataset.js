import { useEffect, useState } from "react";
import { apiUrl, DATASET_ROUTES, IS_LIVE_API } from "./apiConfig";

/*
  useDataset — one hook that every page uses to load a JSON table.

  Two data sources, selected automatically by whether VITE_API_BASE_URL is
  set (see apiConfig.js / .env.example):

  1. Static mode (default today): the Python script (data/generate_sample_data.py)
     writes each pandas table to frontend/public/data/<name>.json as a plain
     array of row objects, e.g.
     customers.json -> [{customer_id: "CUST-0001", churn_probability: 0.27, ...}, ...]
     Vite serves everything under public/ at the site root, so fetching
     "/data/customers.json" works both in `npm run dev` and in the built,
     deployed site -- no server or API layer needed.

  2. Live mode (once the Java + WEKA backend exists): the same dataset name
     is mapped (via DATASET_ROUTES) to a REST path and fetched from the
     backend instead, returning the identical row-array shape documented in
     docs/api/openapi.yaml. No calling code (pages/components) needs to
     change -- they only ever see { data, loading, error, refetch }.

  `refreshKey` (optional) lets a caller force a reload -- e.g. Model
  Diagnostics bumps it after a live model retrain completes so backtest
  metrics / calibration / drift charts pick up the newly retrained numbers
  without a full page reload. `refetch()` does the same thing on demand.
*/
export function useDataset(name, { refreshKey } = {}) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [manualTick, setManualTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(null);

    const url = IS_LIVE_API
      ? apiUrl(DATASET_ROUTES[name] ?? `/${name}`)
      : `${import.meta.env.BASE_URL}data/${name}.json`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load ${name} from ${url} (${res.status})`);
        return res.json();
      })
      .then((json) => {
        if (!cancelled) setData(json);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      });

    return () => {
      cancelled = true;
    };
  }, [name, refreshKey, manualTick]);

  return {
    data,
    loading: data === null && !error,
    error,
    refetch: () => setManualTick((t) => t + 1),
  };
}
