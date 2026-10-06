"""
generate_sample_data.py
========================

Sample data generator for the ChurnCast subscription analytics dashboard
(a custom web dashboard -- see /frontend -- not Power BI).

WHY THIS SCRIPT EXISTS
-----------------------
A real version of this project would get its numbers from a Microsoft Fabric
pipeline and a scikit-learn model trained on historical customer data. Since
this project is the *front end* (the dashboard itself), we don't train a
real model here. Instead, this script simulates a subscription business
and scores each customer's churn risk with a simple, transparent formula
that behaves the way a trained model's output would: a probability between
0 and 1 for every customer, plus the usual model-monitoring numbers
(backtest accuracy, calibration, feature drift, etc).

Every number this script produces is fake, but the *shape* of the data is
realistic: contract types, regions, plans, tenure, usage, and support
tickets all come from Telco-style churn datasets you'd find on Kaggle.

HOW IT WORKS (high level)
--------------------------
1. Create N synthetic customers with realistic attributes.
2. Score each customer's churn risk as a weighted sum of 5 risk factors.
   Storing the weights explicitly (instead of hiding them in a black-box
   model) makes it easy to explain in a demo: "we multiply how inactive a
   customer is by 0.25, how flexible their contract is by 0.20, etc."
3. Sample a synthetic "did they actually churn" outcome from that
   probability, so we have something to grade our own predictions against
   (this is what backtest_metrics.csv, calibration.csv and the AUC number
   are built from).
4. Roll up customer-level data into the company-level tables the dashboard
   needs: a monthly revenue forecast, a cohort retention heatmap, feature
   drift, and a leakage checklist.

Run it with:
    python generate_sample_data.py

It (re)writes CSV files into data/raw/ *and* JSON files into
frontend/public/data/ (what the React dashboard actually fetches at
runtime). The random seed is fixed, so running
it twice in a row produces identical numbers -- that keeps the dashboard
reproducible when you demo it or re-open the PBIX later.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Settings -- change these to make a bigger/smaller sample dataset.
# ---------------------------------------------------------------------------

RANDOM_SEED = 42
N_CUSTOMERS = 500
HISTORY_MONTHS = 12          # how many months of "actuals" we simulate
COHORT_MONTHS_BACK = 15      # how many signup cohorts show up in the heatmap
DRIFT_WINDOW_MONTHS = 3      # signups this recent are treated as the "recent" drift window

OUTPUT_DIR = Path(__file__).parent / "raw"
# The custom dashboard (frontend/) fetches these as static JSON at runtime --
# writing them directly into its public/ folder means "regenerate data" and
# "refresh the dashboard" are always a `python generate_sample_data.py` away.
JSON_OUTPUT_DIR = Path(__file__).parent.parent / "frontend" / "public" / "data"

rng = np.random.default_rng(RANDOM_SEED)

# The report always forecasts "next calendar month" relative to whenever this
# script runs, so re-generating the data keeps the demo looking current.
FORECAST_MONTH = pd.Timestamp.today().normalize().replace(day=1)
TODAY = FORECAST_MONTH - pd.Timedelta(days=1)  # last day of the latest historical month
HISTORY_START = FORECAST_MONTH - pd.DateOffset(months=HISTORY_MONTHS)
HISTORY_MONTHS_LIST = list(pd.date_range(HISTORY_START, periods=HISTORY_MONTHS, freq="MS"))

# Business reference data -----------------------------------------------------

PLAN_PRICES = {"Basic": 19.0, "Standard": 49.0, "Premium": 99.0}
PLAN_WEIGHTS = {"Basic": 0.40, "Standard": 0.40, "Premium": 0.20}

CONTRACT_TYPES = ["Month-to-month", "One year", "Two year"]
CONTRACT_WEIGHTS = [0.55, 0.30, 0.15]
# A month-to-month customer can leave any time, so they carry the most risk.
CONTRACT_RISK = {"Month-to-month": 1.00, "One year": 0.40, "Two year": 0.15}
CONTRACT_DISCOUNT = {"Month-to-month": 0.00, "One year": 0.05, "Two year": 0.10}

REGIONS = ["North", "South", "East", "West"]

FIRST_NAMES = [
    "Aarav", "Bella", "Carlos", "Diya", "Ethan", "Farah", "Gabriel", "Hana",
    "Ivan", "Jasmine", "Kenji", "Layla", "Miguel", "Nora", "Omar", "Priya",
    "Quinn", "Rosa", "Sam", "Talia", "Umar", "Vera", "Wei", "Ximena", "Yusuf", "Zara",
]
LAST_NAMES = [
    "Anderson", "Brooks", "Chen", "Davies", "Espinoza", "Fischer", "Garcia",
    "Haddad", "Ibrahim", "Johansson", "Kim", "Lopez", "Martins", "Nguyen",
    "O'Connor", "Patel", "Quintero", "Rossi", "Silva", "Tanaka",
]

# Churn-risk formula weights -- these five factors must add up to 1.0, and
# they double as the "feature contribution" weights used in the
# explainability chart on the Customer Risk Explorer page.
CHURN_WEIGHTS = {
    "low_usage": 0.35,       # the less a customer uses the product, the higher the risk
    "inactivity": 0.25,      # days since they were last seen logging in
    "contract_flex": 0.20,   # month-to-month contracts are easiest to cancel
    "support_tickets": 0.10, # lots of recent support tickets signals frustration
    "low_tenure": 0.10,      # brand-new customers haven't formed a habit yet
}
assert abs(sum(CHURN_WEIGHTS.values()) - 1.0) < 1e-9

FEATURE_LABELS = {
    "low_usage": "Low product usage",
    "inactivity": "Days since last login",
    "contract_flex": "Month-to-month contract",
    "support_tickets": "Recent support tickets",
    "low_tenure": "Short tenure",
}


def make_customer_names(n: int) -> list[str]:
    """Combine first/last name pools into n plausible (fake) customer names."""
    first = rng.choice(FIRST_NAMES, size=n)
    last = rng.choice(LAST_NAMES, size=n)
    return [f"{f} {l}" for f, l in zip(first, last)]


# ---------------------------------------------------------------------------
# Step 1: customers table
# ---------------------------------------------------------------------------

def generate_customers() -> tuple[pd.DataFrame, dict, np.ndarray]:
    """Create the customer-level table the whole report is built on."""
    n = N_CUSTOMERS

    # Signups spread over the last two years, weighted towards being a bit
    # more recent (a growing subscription business signs up more people now
    # than it did two years ago).
    days_back = rng.triangular(left=0, mode=60, right=730, size=n).astype(int)
    signup_date = pd.to_datetime(TODAY) - pd.to_timedelta(days_back, unit="D")

    contract_type = rng.choice(CONTRACT_TYPES, size=n, p=CONTRACT_WEIGHTS)
    plan = rng.choice(list(PLAN_PRICES.keys()), size=n, p=list(PLAN_WEIGHTS.values()))
    region = rng.choice(REGIONS, size=n)

    tenure_months = (pd.to_datetime(TODAY) - signup_date).days // 30
    tenure_months = pd.Series(tenure_months).clip(lower=1)
    is_recent_signup = days_back <= (DRIFT_WINDOW_MONTHS * 30)

    # --- usage & support signals -------------------------------------------
    # Recent signups get a lower usage score and slightly more tickets on
    # average. That gap is the "synthetic drift" the Model Diagnostics page
    # is meant to catch -- see compute_drift_metrics() below.
    usage_mean = np.where(is_recent_signup, 55.0, 68.0)
    usage_score = rng.normal(loc=usage_mean, scale=15.0, size=n).clip(0, 100)

    ticket_lambda = np.where(is_recent_signup, 1.8, 1.0)
    support_tickets_90d = rng.poisson(lam=ticket_lambda, size=n).clip(0, 8)

    # Customers who barely use the product tend to have logged in longer ago.
    days_since_active = (
        (100 - usage_score) * 0.8 + rng.normal(0, 8, size=n)
    ).clip(0, 90).astype(int)
    last_active_date = pd.to_datetime(TODAY) - pd.to_timedelta(days_since_active, unit="D")

    # --- monthly revenue ------------------------------------------------
    base_price = np.array([PLAN_PRICES[p] for p in plan])
    discount = np.array([CONTRACT_DISCOUNT[c] for c in contract_type])
    monthly_revenue = (base_price * (1 - discount) * (1 + rng.normal(0, 0.05, size=n))).round(2)

    # --- churn risk score -------------------------------------------------
    # Each component is scaled to 0-1 so the weights above are comparable.
    contract_risk = np.array([CONTRACT_RISK[c] for c in contract_type])
    components = {
        "low_usage": 1 - usage_score / 100,
        "inactivity": (days_since_active / 90).clip(0, 1),
        "contract_flex": contract_risk,
        "support_tickets": (support_tickets_90d / 8).clip(0, 1),
        "low_tenure": 1 - (tenure_months / 36).clip(0, 1),
    }
    risk_score = sum(CHURN_WEIGHTS[k] * v for k, v in components.items())
    risk_score = risk_score + rng.normal(0, 0.05, size=n)  # a little noise, like real life
    churn_probability = np.clip(risk_score, 0.02, 0.98)
    churn_flag_thresholded = (churn_probability >= 0.5).astype(int)

    # A synthetic "ground truth": did this customer actually churn last
    # month? We sample it from their own probability so it's noisy, not a
    # perfect mirror of churn_probability -- exactly like a real model would
    # face when it's graded against history.
    did_churn_last_month = rng.binomial(1, churn_probability)

    predicted_revenue_loss = (monthly_revenue * churn_probability).round(2)

    # This one column is deliberately unrealistic: it's built FROM the
    # outcome it claims to predict (a support agent logging "I called this
    # account to try to save it" mostly *after* seeing them struggle,
    # occasionally getting it wrong). It exists purely so the Model
    # Diagnostics "data leakage checklist" has a genuine example to flag --
    # every other column in this table is a fair, pre-outcome feature.
    mislabelled = rng.random(n) < 0.12
    retention_call_flag = np.where(mislabelled, 1 - did_churn_last_month, did_churn_last_month)

    customers = pd.DataFrame({
        "customer_id": [f"CUST-{i:04d}" for i in range(1, n + 1)],
        "customer_name": make_customer_names(n),
        "signup_date": signup_date.strftime("%Y-%m-%d"),
        "last_active_date": last_active_date.strftime("%Y-%m-%d"),
        "contract_type": contract_type,
        "plan": plan,
        "region": region,
        "tenure_months": tenure_months.astype(int),
        "monthly_revenue": monthly_revenue,
        "usage_score": usage_score.round(1),
        "support_tickets_90d": support_tickets_90d.astype(int),
        "days_since_active": days_since_active.astype(int),
        "churn_probability": churn_probability.round(4),
        "churn_flag_thresholded": churn_flag_thresholded,
        "predicted_revenue_loss": predicted_revenue_loss,
        "did_churn_last_month": did_churn_last_month,
        "retention_call_flag": retention_call_flag,
    })

    # components and is_recent_signup are internal details of how the mock
    # data was built (not columns Power BI needs) -- returned separately so
    # generate_feature_contributions() and compute_drift_metrics() can reuse
    # them without smuggling extra data through the DataFrame itself.
    return customers, components, is_recent_signup


# ---------------------------------------------------------------------------
# Step 2: per-customer revenue history (drives the sparkline in the explorer)
# ---------------------------------------------------------------------------

def generate_revenue_history(customers: pd.DataFrame) -> pd.DataFrame:
    """12 months of revenue per customer, with a soft downward drift for
    customers who are already at high risk of churning (their usage was
    fading before they left -- a common real-world pattern)."""
    rows = []
    for _, cust in customers.iterrows():
        for month_idx, month in enumerate(HISTORY_MONTHS_LIST):
            noise = rng.normal(0, 0.04)
            decline = 0.0
            if cust["churn_probability"] > 0.6 and month_idx >= HISTORY_MONTHS - 3:
                months_into_decline = month_idx - (HISTORY_MONTHS - 4)
                decline = -0.06 * months_into_decline * cust["churn_probability"]
            value = max(cust["monthly_revenue"] * (1 + noise + decline), 0)
            rows.append((cust["customer_id"], month.strftime("%Y-%m-%d"), round(value, 2)))
    return pd.DataFrame(rows, columns=["customer_id", "month", "revenue"])


# ---------------------------------------------------------------------------
# Step 3: explainability -- turn the risk formula into per-customer bars
# ---------------------------------------------------------------------------

def generate_feature_contributions(customers: pd.DataFrame, components: dict) -> pd.DataFrame:
    """Express each customer's churn score as 5 signed contributions
    (their factor minus the population-average factor, times its weight).
    This is a simplified stand-in for SHAP values: positive means "this
    pushed the customer's risk up", negative means "this pulled it down"."""
    rows = []
    for key, values in components.items():
        baseline = values.mean()
        contribution = CHURN_WEIGHTS[key] * (values - baseline)
        for customer_id, value in zip(customers["customer_id"], contribution):
            rows.append((customer_id, FEATURE_LABELS[key], round(float(value), 4)))

    contributions = pd.DataFrame(rows, columns=["customer_id", "feature_name", "contribution"])
    contributions["abs_contribution"] = contributions["contribution"].abs()
    contributions["rank"] = (
        contributions.groupby("customer_id")["abs_contribution"]
        .rank(method="first", ascending=False)
        .astype(int)
    )
    return contributions.drop(columns="abs_contribution").sort_values(["customer_id", "rank"])


# ---------------------------------------------------------------------------
# Small, dependency-free metric helpers (numpy only -- no scikit-learn).
# Writing these out longhand keeps the "how is this number calculated?"
# question answerable in a hackathon Q&A.
# ---------------------------------------------------------------------------

def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Percentage Error, as a percentage."""
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    return float(np.mean(np.abs((actual - predicted) / actual)) * 100)


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Root Mean Squared Error, in the same units as the data."""
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """AUC via the rank-sum (Mann-Whitney U) method: rank every prediction,
    then check how often a random "churned" customer outranks a random
    "stayed" customer. 0.5 = coin flip, 1.0 = perfect separation."""
    y_true, y_score = np.asarray(y_true), np.asarray(y_score)
    ranks = pd.Series(y_score).rank().to_numpy()
    n_pos, n_neg = y_true.sum(), (1 - y_true).sum()
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    sum_ranks_pos = ranks[y_true == 1].sum()
    return float((sum_ranks_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def ks_statistic(sample_a: np.ndarray, sample_b: np.ndarray) -> float:
    """Kolmogorov-Smirnov statistic: the biggest gap between two samples'
    cumulative distributions. Bigger gap = more evidence the two samples
    come from different distributions (i.e. the feature has drifted)."""
    sample_a, sample_b = np.sort(sample_a), np.sort(sample_b)
    combined = np.sort(np.concatenate([sample_a, sample_b]))
    cdf_a = np.searchsorted(sample_a, combined, side="right") / len(sample_a)
    cdf_b = np.searchsorted(sample_b, combined, side="right") / len(sample_b)
    return float(np.max(np.abs(cdf_a - cdf_b)))


# ---------------------------------------------------------------------------
# Step 4: company-level monthly revenue -- actuals, trend line, and forecast
# ---------------------------------------------------------------------------

def generate_monthly_revenue(revenue_history: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Roll up per-customer revenue into a company-level monthly total, fit a
    straight-line trend through history, and project one month ahead with a
    95%-style prediction interval built from the trend's own past errors."""
    monthly_actual = (
        revenue_history.groupby("month")["revenue"].sum().reindex(
            [m.strftime("%Y-%m-%d") for m in HISTORY_MONTHS_LIST]
        )
    )
    month_index = np.arange(HISTORY_MONTHS)
    actual_values = monthly_actual.to_numpy()

    # Fit y = a*x + b through the 12 historical points.
    slope, intercept = np.polyfit(month_index, actual_values, deg=1)
    trend_line = slope * month_index + intercept
    residual_std = np.std(actual_values - trend_line, ddof=1)

    point_forecast = slope * HISTORY_MONTHS + intercept
    forecast_low = point_forecast - 1.96 * residual_std
    forecast_high = point_forecast + 1.96 * residual_std

    # Walk-forward backtest: pretend we only knew the past when predicting
    # each month, so the MAPE trend sparkline shows genuine one-step-ahead
    # errors instead of an in-sample fit (which would look unrealistically
    # good). The first two months don't have enough history to fit a line.
    walk_forward_errors = [np.nan, np.nan]
    walk_forward_predictions = [np.nan, np.nan]
    for i in range(2, HISTORY_MONTHS):
        s, b = np.polyfit(month_index[:i], actual_values[:i], deg=1)
        pred_i = s * i + b
        walk_forward_predictions.append(pred_i)
        walk_forward_errors.append(abs((actual_values[i] - pred_i) / actual_values[i]) * 100)

    rows = []
    for i, month in enumerate(HISTORY_MONTHS_LIST):
        is_last_historical = i == HISTORY_MONTHS - 1
        rows.append({
            "month": month.strftime("%Y-%m-%d"),
            "actual_revenue": round(float(actual_values[i]), 2),
            # Forecast line only "starts" at the last actual month, so it
            # visually connects to the point forecast that follows it.
            "forecast_revenue": round(float(actual_values[i]), 2) if is_last_historical else None,
            "forecast_low": round(float(actual_values[i]), 2) if is_last_historical else None,
            "forecast_high": round(float(actual_values[i]), 2) if is_last_historical else None,
            "is_forecast_month": 0,
            "mape_trend": None if np.isnan(walk_forward_errors[i]) else round(walk_forward_errors[i], 2),
        })
    rows.append({
        "month": FORECAST_MONTH.strftime("%Y-%m-%d"),
        "actual_revenue": None,
        "forecast_revenue": round(float(point_forecast), 2),
        "forecast_low": round(float(forecast_low), 2),
        "forecast_high": round(float(forecast_high), 2),
        "is_forecast_month": 1,
        "mape_trend": None,
    })
    monthly_revenue_df = pd.DataFrame(rows)

    backtest_actuals = actual_values[2:]
    backtest_predictions = np.array(walk_forward_predictions[2:])
    summary = {
        "mape": mape(backtest_actuals, backtest_predictions),
        "rmse": rmse(backtest_actuals, backtest_predictions),
    }
    return monthly_revenue_df, summary


# ---------------------------------------------------------------------------
# Step 5: cohort retention heatmap
# ---------------------------------------------------------------------------

def generate_cohort_retention() -> pd.DataFrame:
    """Simulate a retention curve per signup cohort: each cohort loses a
    small, constant fraction of members every month (a geometric decay,
    the simplest realistic retention curve). One extra month per cohort is
    marked as a forecast, matching the "forecasted next-month retention"
    requirement."""
    rows = []
    cohort_months = pd.date_range(
        FORECAST_MONTH - pd.DateOffset(months=COHORT_MONTHS_BACK), periods=COHORT_MONTHS_BACK, freq="MS"
    )
    for cohort_idx, cohort_month in enumerate(cohort_months):
        months_elapsed = (TODAY.year - cohort_month.year) * 12 + (TODAY.month - cohort_month.month)
        # A per-cohort survival rate between 93% and 97% retained each month.
        survival_rate = rng.uniform(0.93, 0.97)
        max_month_shown = min(months_elapsed + 1, 11)  # +1 gives us the forecast column
        for months_since_signup in range(0, max_month_shown + 1):
            noise = rng.normal(0, 1.5)
            retention_rate = np.clip(100 * survival_rate ** months_since_signup + noise, 0, 100)
            is_forecast = int(months_since_signup == months_elapsed + 1)
            rows.append({
                "signup_month": cohort_month.strftime("%Y-%m"),
                "cohort_order": cohort_idx,
                "months_since_signup": months_since_signup,
                "retention_rate": round(float(retention_rate), 1),
                "is_forecast": is_forecast,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 6: model diagnostics -- backtest metrics, calibration, drift, leakage
# ---------------------------------------------------------------------------

def compute_backtest_metrics(customers: pd.DataFrame, revenue_summary: dict) -> pd.DataFrame:
    y_true = customers["did_churn_last_month"].to_numpy()
    y_score = customers["churn_probability"].to_numpy()
    y_pred = customers["churn_flag_thresholded"].to_numpy()

    true_positive = int(((y_pred == 1) & (y_true == 1)).sum())
    false_positive = int(((y_pred == 1) & (y_true == 0)).sum())
    false_negative = int(((y_pred == 0) & (y_true == 1)).sum())
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) else 0.0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) else 0.0

    top_10 = customers.nlargest(10, "churn_probability")
    precision_at_10 = float(top_10["did_churn_last_month"].mean())

    rows = [
        ("Revenue MAPE", round(revenue_summary["mape"], 2), "Revenue", f"{revenue_summary['mape']:.1f}%"),
        ("Revenue RMSE", round(revenue_summary["rmse"], 2), "Revenue", f"${revenue_summary['rmse']:,.0f}"),
        ("Churn AUC", round(roc_auc(y_true, y_score), 3), "Churn", f"{roc_auc(y_true, y_score):.2f}"),
        ("Churn Precision", round(precision, 3), "Churn", f"{precision * 100:.0f}%"),
        ("Churn Recall", round(recall, 3), "Churn", f"{recall * 100:.0f}%"),
        ("Precision @ Top 10", round(precision_at_10, 3), "Churn", f"{precision_at_10 * 100:.0f}%"),
    ]
    return pd.DataFrame(rows, columns=["metric_name", "metric_value", "metric_type", "metric_display"])


def compute_calibration(customers: pd.DataFrame) -> pd.DataFrame:
    """Sort customers into 10 probability deciles and compare the average
    predicted probability in each bucket to what actually happened. A
    well-calibrated model keeps these two numbers close together."""
    bucket_edges = np.linspace(0, 1, 11)
    bucket_labels = [f"{int(bucket_edges[i] * 100)}-{int(bucket_edges[i + 1] * 100)}%" for i in range(10)]
    buckets = pd.cut(customers["churn_probability"], bins=bucket_edges, labels=bucket_labels, include_lowest=True)

    calibration = (
        customers.groupby(buckets, observed=True)
        .agg(predicted_avg=("churn_probability", "mean"), actual_rate=("did_churn_last_month", "mean"),
             customer_count=("customer_id", "count"))
        .reindex(bucket_labels)
        .reset_index(names="bucket_label")
    )
    calibration["bucket_order"] = range(len(calibration))
    calibration["predicted_avg"] = calibration["predicted_avg"].round(3)
    calibration["actual_rate"] = calibration["actual_rate"].round(3)
    calibration = calibration.dropna(subset=["customer_count"])
    calibration["customer_count"] = calibration["customer_count"].astype(int)
    return calibration


DRIFT_FEATURES = ["usage_score", "support_tickets_90d", "monthly_revenue", "days_since_active"]
DRIFT_THRESHOLD = 0.15  # KS statistics above this are flagged as drifted


def compute_drift_metrics(customers: pd.DataFrame, is_recent_signup) -> pd.DataFrame:
    """Compare "recent signups" against "older signups" for a handful of
    features. usage_score/support_tickets_90d/days_since_active were built
    with a deliberate gap between the two groups (see generate_customers),
    so they should trip the drift flag; monthly_revenue was not, and acts as
    the "nothing to see here" control example."""
    is_recent = is_recent_signup
    rows = []
    for feature in DRIFT_FEATURES:
        baseline = customers.loc[~is_recent, feature].to_numpy(dtype=float)
        recent = customers.loc[is_recent, feature].to_numpy(dtype=float)
        ks_stat = ks_statistic(baseline, recent)
        rows.append({
            "feature_name": feature,
            "ks_statistic": round(ks_stat, 3),
            "drift_flag": int(ks_stat > DRIFT_THRESHOLD),
            "baseline_mean": round(float(baseline.mean()), 2),
            "recent_mean": round(float(recent.mean()), 2),
        })
    return pd.DataFrame(rows)


def generate_drift_distributions(customers: pd.DataFrame, is_recent_signup) -> pd.DataFrame:
    """Bucket each drift feature into 8 bins per group, so the report can
    draw a small-multiples histogram (baseline vs. recent) per feature."""
    is_recent = is_recent_signup
    rows = []
    for feature in DRIFT_FEATURES:
        values = customers[feature].to_numpy(dtype=float)
        bin_edges = np.linspace(values.min(), values.max(), 9)
        bin_labels = [f"{bin_edges[i]:.0f}-{bin_edges[i + 1]:.0f}" for i in range(8)]
        for period_name, mask in [("Baseline", ~is_recent), ("Recent", is_recent)]:
            group_values = values[mask]
            bucket_index = np.clip(np.digitize(group_values, bin_edges[1:-1]), 0, 7)
            counts = np.bincount(bucket_index, minlength=8)
            proportions = counts / counts.sum()
            for i in range(8):
                rows.append({
                    "feature_name": feature,
                    "period": period_name,
                    "bucket_label": bin_labels[i],
                    "bucket_order": i,
                    "proportion": round(float(proportions[i]), 4),
                })
    return pd.DataFrame(rows)


def compute_leakage_checklist(customers: pd.DataFrame) -> pd.DataFrame:
    """Correlate each raw feature against the actual outcome
    (did_churn_last_month). A feature that correlates almost perfectly with
    the label is worth double-checking for leakage -- it may only "predict"
    churn because it was measured after the customer already left."""
    label = customers["did_churn_last_month"].to_numpy(dtype=float)
    numeric_features = {
        "usage_score": customers["usage_score"],
        "days_since_active": customers["days_since_active"],
        "support_tickets_90d": customers["support_tickets_90d"],
        "tenure_months": customers["tenure_months"],
        "monthly_revenue": customers["monthly_revenue"],
        "contract_flexibility": customers["contract_type"].map(CONTRACT_RISK),
        "retention_call_flag": customers["retention_call_flag"],
    }
    custom_notes = {
        "retention_call_flag": (
            "This is logged by the support team *after* they decide an account looks "
            "shaky, so it's downstream of the very thing we're trying to predict. "
            "Drop it from training, or only use it if it was recorded before the "
            "churn outcome was known."
        ),
    }
    rows = []
    for name, series in numeric_features.items():
        corr = float(np.corrcoef(series.to_numpy(dtype=float), label)[0, 1])
        flagged = abs(corr) > 0.5
        note = custom_notes.get(name) or (
            "Correlates strongly with the outcome -- confirm this value was known "
            "*before* the churn event, not measured after it."
            if flagged
            else "No strong correlation with the outcome; looks safe to keep."
        )
        rows.append({
            "feature_name": name,
            "correlation_with_label": round(corr, 3),
            "leakage_flag": int(flagged),
            "note": note,
        })
    return pd.DataFrame(rows).sort_values("correlation_with_label", key=abs, ascending=False)


def generate_model_meta(backtest_metrics: pd.DataFrame) -> pd.DataFrame:
    mape_value = backtest_metrics.loc[backtest_metrics["metric_name"] == "Revenue MAPE", "metric_value"].iloc[0]
    auc_value = backtest_metrics.loc[backtest_metrics["metric_name"] == "Churn AUC", "metric_value"].iloc[0]
    holdout_start = HISTORY_MONTHS_LIST[-3]
    return pd.DataFrame([{
        "last_trained_date": TODAY.strftime("%Y-%m-%d"),
        "next_scheduled_retrain": FORECAST_MONTH.strftime("%Y-%m-%d"),
        "holdout_start": holdout_start.strftime("%Y-%m-%d"),
        "holdout_end": TODAY.strftime("%Y-%m-%d"),
        "sample_size": N_CUSTOMERS,
        "holdout_mape": mape_value,
        "holdout_auc": auc_value,
    }])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    customers, components, is_recent_signup = generate_customers()
    revenue_history = generate_revenue_history(customers)
    feature_contributions = generate_feature_contributions(customers, components)
    monthly_revenue, revenue_summary = generate_monthly_revenue(revenue_history)
    cohort_retention = generate_cohort_retention()
    backtest_metrics = compute_backtest_metrics(customers, revenue_summary)
    calibration = compute_calibration(customers)
    drift_metrics = compute_drift_metrics(customers, is_recent_signup)
    drift_distributions = generate_drift_distributions(customers, is_recent_signup)
    leakage_checklist = compute_leakage_checklist(customers)
    model_meta = generate_model_meta(backtest_metrics)

    tables = {
        "customers": customers,
        "revenue_history": revenue_history,
        "feature_contributions": feature_contributions,
        "monthly_revenue": monthly_revenue,
        "cohort_retention": cohort_retention,
        "backtest_metrics": backtest_metrics,
        "calibration": calibration,
        "drift_metrics": drift_metrics,
        "drift_distributions": drift_distributions,
        "leakage_checklist": leakage_checklist,
        "model_meta": model_meta,
    }

    for name, table in tables.items():
        table.to_csv(OUTPUT_DIR / f"{name}.csv", index=False, encoding="utf-8")
        # records orientation -> a plain JSON array of row objects, the
        # simplest possible shape for the frontend to `fetch()` and map over.
        table.to_json(JSON_OUTPUT_DIR / f"{name}.json", orient="records", indent=2)

    print(f"Forecasting month: {FORECAST_MONTH.strftime('%B %Y')}")
    print(f"Generated {N_CUSTOMERS} customers, {len(revenue_history)} revenue-history rows.")
    print(f"Revenue backtest -> MAPE {revenue_summary['mape']:.1f}%, RMSE ${revenue_summary['rmse']:,.0f}")
    print(f"Wrote {len(tables)} CSV files to {OUTPUT_DIR}")
    print(f"Wrote {len(tables)} JSON files to {JSON_OUTPUT_DIR}")


if __name__ == "__main__":
    main()
