/*
  churnSimulation.js — the "what-if usage drops further" client-side model.

  This is intentionally a simple, transparent linear rule rather than a real
  model call, exactly like the mock churn_probability itself: every extra
  percentage point of usage drop pushes churn risk up by a fixed amount,
  capped between 0 and 1. The 0.4 slope means a full 100% usage drop adds at
  most 0.4 (40 percentage points) of churn probability.

  Keeping the formula here (instead of inline in a component) means the
  Customer Risk Explorer page and any future "what-if" surface reuse the
  exact same rule, and it can be unit-tested on its own.
*/
const USAGE_DROP_SLOPE = 0.4;

export function simulateChurnProbability(baseProbability, usageDropPercent) {
  const bump = (usageDropPercent / 100) * USAGE_DROP_SLOPE;
  return Math.min(1, Math.max(0, baseProbability + bump));
}

export function simulateRevenueImpact(monthlyRevenue, baseProbability, simulatedProbability) {
  return monthlyRevenue * (simulatedProbability - baseProbability);
}
