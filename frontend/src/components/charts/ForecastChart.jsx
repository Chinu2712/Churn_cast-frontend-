import {
  ResponsiveContainer, ComposedChart, Area, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceDot,
} from "recharts";
import { formatCurrency, formatDate } from "../../utils/format";

/*
  ForecastChart — historical actual revenue, the shaded prediction interval,
  and the next-month point forecast, all in one Recharts ComposedChart.

  The shaded band is drawn as a stacked Area: an invisible "floor" area up to
  forecast_low, then a visible area from forecast_low to forecast_high. Both
  only have values on rows where is_forecast_month/forecast_low are set, so
  the band only appears over the historical-to-forecast transition.
*/
export default function ForecastChart({ rows }) {
  const chartData = rows.map((r) => ({
    ...r,
    bandFloor: r.forecast_low,
    bandHeight: r.forecast_low != null ? r.forecast_high - r.forecast_low : null,
  }));
  const forecastPoint = chartData.find((r) => r.is_forecast_month === 1);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="month"
          tickFormatter={(v) => formatDate(v, { year: undefined })}
          stroke="var(--text-light)"
          fontSize={11}
        />
        <YAxis
          tickFormatter={(v) => formatCurrency(v)}
          stroke="var(--text-light)"
          fontSize={11}
          width={70}
        />
        <Tooltip
          formatter={(value, name) => [formatCurrency(value), name]}
          labelFormatter={(v) => formatDate(v)}
          contentStyle={{ background: "var(--card-bg)", border: "1px solid var(--border)", fontSize: 12 }}
        />
        {/* invisible floor so the visible band starts at forecast_low, not 0 */}
        <Area dataKey="bandFloor" stackId="band" stroke="none" fill="transparent" name="" legendType="none" />
        <Area
          dataKey="bandHeight"
          stackId="band"
          stroke="none"
          fill="var(--accent-light)"
          fillOpacity={0.35}
          name="Prediction interval"
        />
        <Line
          dataKey="actual_revenue"
          stroke="var(--accent)"
          strokeWidth={2.5}
          dot={{ r: 3 }}
          name="Actual revenue"
          connectNulls
        />
        <Line
          dataKey="forecast_revenue"
          stroke="var(--accent)"
          strokeWidth={2.5}
          strokeDasharray="6 5"
          dot={{ r: 3 }}
          name="Forecast"
          connectNulls
        />
        {forecastPoint && (
          <ReferenceDot
            x={forecastPoint.month}
            y={forecastPoint.forecast_revenue}
            r={6}
            fill="var(--accent)"
            stroke="var(--card-bg)"
            strokeWidth={2}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
