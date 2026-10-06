/*
  deriveFields.js — presentation-layer categorizations computed in the
  frontend instead of a DAX/SQL layer.

  These two buckets used to be DAX calculated columns in an earlier,
  Power-BI-based version of this project. Now that the dashboard is a
  plain React app reading raw JSON, the simplest and most transparent place
  for "which bucket does this number fall into?" logic is right here in
  plain, readable JavaScript -- anyone reviewing the code sees the exact
  thresholds without needing to open a separate BI tool.
*/

export function riskBucketFromProbability(probability) {
  if (probability >= 0.6) return "High";
  if (probability >= 0.3) return "Medium";
  return "Low";
}

export function tenureBucketFromMonths(months) {
  if (months < 6) return "0-6 months";
  if (months < 12) return "6-12 months";
  if (months < 24) return "12-24 months";
  return "24+ months";
}

/** Adds "Risk Bucket" and "Tenure Bucket" to a raw customer row. */
export function withDerivedCustomerFields(customer) {
  return {
    ...customer,
    "Risk Bucket": riskBucketFromProbability(customer.churn_probability),
    "Tenure Bucket": tenureBucketFromMonths(customer.tenure_months),
  };
}
