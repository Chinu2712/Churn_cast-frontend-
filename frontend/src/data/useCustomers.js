import { useMemo } from "react";
import { useDataset } from "./useDataset";
import { withDerivedCustomerFields } from "../utils/deriveFields";

/*
  useCustomers — a thin wrapper around useDataset("customers") that adds
  the "Risk Bucket" / "Tenure Bucket" derived fields (see deriveFields.js)
  before any page gets to see the data. Every page that needs the customer
  table should use this hook instead of useDataset("customers") directly,
  so the derived fields are always present.
*/
export function useCustomers(options) {
  const { data, loading, error, refetch } = useDataset("customers", options);
  const enriched = useMemo(() => (data ? data.map(withDerivedCustomerFields) : null), [data]);
  return { data: enriched, loading, error, refetch };
}
