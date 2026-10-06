import { useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import PageLayout from "../components/layout/PageLayout";
import TopBar from "../components/layout/TopBar";
import { Section } from "../components/ui/Card";
import KpiCard from "../components/ui/KpiCard";
import Badge from "../components/ui/Badge";
import DataState from "../components/ui/DataState";
import FeatureBarChart from "../components/charts/FeatureBarChart";
import { useDataset } from "../data/useDataset";
import { useCustomers } from "../data/useCustomers";
import { formatCurrency, formatPercent, formatDate } from "../utils/format";

/*
  CustomerDetailPage — the "drillthrough" destination. In Power BI this
  would be a hidden page reached by right-click > Drillthrough; here it's
  just a normal React Router route (/customer/:id) navigated to via a link,
  which is the natural web equivalent.
*/
export default function CustomerDetailPage() {
  const { id } = useParams();
  const customers = useCustomers();
  const revenueHistory = useDataset("revenue_history");
  const featureContributions = useDataset("feature_contributions");

  const ready = customers.data && revenueHistory.data && featureContributions.data;
  const loading = !ready && ![customers, revenueHistory, featureContributions].some((d) => d.error);
  const error = [customers, revenueHistory, featureContributions].find((d) => d.error)?.error;

  const customer = ready ? customers.data.find((c) => c.customer_id === id) : null;
  const history = useMemo(
    () => (ready ? revenueHistory.data.filter((r) => r.customer_id === id) : []),
    [ready, revenueHistory.data, id]
  );
  const contributions = useMemo(
    () => (ready ? featureContributions.data.filter((f) => f.customer_id === id).sort((a, b) => a.rank - b.rank) : []),
    [ready, featureContributions.data, id]
  );

  return (
    <PageLayout>
      <TopBar title="Customer Detail" />
      <Link to="/explorer" className="btn" style={{ display: "inline-block", marginBottom: 16, textDecoration: "none" }}>
        &larr; Back to Customer Risk Explorer
      </Link>
      <DataState loading={loading} error={error}>
        {ready && !customer && <p className="error-text">No customer found with id "{id}".</p>}
        {ready && customer && (
          <>
            <div className="grid" style={{ gridTemplateColumns: "repeat(4, 1fr)", marginBottom: 16 }}>
              <KpiCard label="Customer" value={customer.customer_name} />
              <KpiCard label="Churn Probability" value={formatPercent(customer.churn_probability)} tone="bad" />
              <KpiCard label="Monthly Revenue" value={formatCurrency(customer.monthly_revenue, { cents: true })} />
              <KpiCard label="Risk Bucket" value={<Badge>{customer["Risk Bucket"]}</Badge>} />
            </div>

            <div className="grid" style={{ gridTemplateColumns: "1fr", marginBottom: 16 }}>
              <Section title="Profile">
                <table>
                  <tbody>
                    <Row label="Signup date" value={formatDate(customer.signup_date)} />
                    <Row label="Last active" value={formatDate(customer.last_active_date)} />
                    <Row label="Contract type" value={customer.contract_type} />
                    <Row label="Plan" value={customer.plan} />
                    <Row label="Region" value={customer.region} />
                    <Row label="Tenure" value={`${customer.tenure_months} months`} />
                    <Row label="Support tickets (last 90 days)" value={customer.support_tickets_90d} />
                    <Row label="Predicted revenue loss" value={formatCurrency(customer.predicted_revenue_loss, { cents: true })} />
                  </tbody>
                </table>
              </Section>
            </div>

            <div className="grid" style={{ gridTemplateColumns: "1.3fr 1fr" }}>
              <Section title="Revenue History">
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={history} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="month" tickFormatter={(v) => formatDate(v, { year: undefined })} fontSize={11} stroke="var(--text-light)" />
                    <YAxis tickFormatter={(v) => formatCurrency(v)} fontSize={11} stroke="var(--text-light)" width={65} />
                    <Tooltip
                      formatter={(v) => formatCurrency(v, { cents: true })}
                      labelFormatter={(v) => formatDate(v)}
                      contentStyle={{ background: "var(--card-bg)", border: "1px solid var(--border)", fontSize: 12 }}
                    />
                    <Line dataKey="revenue" stroke="var(--accent)" strokeWidth={2.5} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </Section>

              <Section title="Explainability" subtitle="— top 5 feature contributions">
                <FeatureBarChart contributions={contributions} />
              </Section>
            </div>
          </>
        )}
      </DataState>
    </PageLayout>
  );
}

function Row({ label, value }) {
  return (
    <tr>
      <td style={{ color: "var(--text-light)", width: "50%" }}>{label}</td>
      <td>{value}</td>
    </tr>
  );
}
