"""
ONE-TIME SCAFFOLDING SCRIPT -- not part of the delivered project.

Hand-typing ~16 TMDL files (each needing exact tab indentation and unique
GUIDs) invites copy-paste mistakes. This script generates them
programmatically from a single column/measure spec below, then gets
deleted -- the generated .tmdl files are the real deliverable, exactly as
if they had been produced by Power BI Desktop itself.
"""
import uuid
from pathlib import Path

ROOT = Path(__file__).parent
MODEL_DIR = ROOT / "ChurnCast.SemanticModel" / "definition"
TABLES_DIR = MODEL_DIR / "tables"
DATA_PATH = str(ROOT / "data" / "raw") + "\\"

PQ_TYPE = {"string": "type text", "int64": "Int64.Type", "double": "type number", "dateTime": "type date"}


def guid() -> str:
    return str(uuid.uuid4())


def q(name: str) -> str:
    """Quote a TMDL name if it needs it (spaces, %, leading digit, etc.)."""
    if name.replace("_", "").isalnum() and not name[0].isdigit():
        return name
    return "'" + name.replace("'", "''") + "'"


def render_column(name, dtype, agg, fmt=None, hidden=False, sort_by=None, folder=None, desc=None) -> str:
    lines = []
    if desc:
        lines.append(f"\t/// {desc}")
    lines.append(f"\tcolumn {q(name)}")
    lines.append(f"\t\tdataType: {dtype}")
    if hidden:
        lines.append("\t\tisHidden")
    if fmt:
        lines.append(f"\t\tformatString: {fmt}")
    if folder:
        lines.append(f"\t\tdisplayFolder: {folder}")
    lines.append(f"\t\tlineageTag: {guid()}")
    lines.append(f"\t\tsummarizeBy: {agg}")
    lines.append(f"\t\tsourceColumn: {name}")
    if sort_by:
        lines.append(f"\t\tsortByColumn: {sort_by}")
    lines.append("")
    lines.append("\t\tannotation SummarizationSetBy = Automatic")
    return "\n".join(lines)


def render_calculated_column(name, dax, dtype, agg, fmt=None, desc=None) -> str:
    lines = []
    if desc:
        lines.append(f"\t/// {desc}")
    lines.append(f"\tcolumn {q(name)} = {dax}")
    lines.append(f"\t\tdataType: {dtype}")
    if fmt:
        lines.append(f"\t\tformatString: {fmt}")
    lines.append(f"\t\tlineageTag: {guid()}")
    lines.append(f"\t\tsummarizeBy: {agg}")
    lines.append("")
    lines.append("\t\tannotation SummarizationSetBy = Automatic")
    return "\n".join(lines)


def render_measure(name, dax, fmt=None, folder=None, desc=None) -> str:
    lines = []
    if desc:
        lines.append(f"\t/// {desc}")
    lines.append(f"\tmeasure {q(name)} = {dax}")
    if fmt:
        lines.append(f"\t\tformatString: {fmt}")
    if folder:
        lines.append(f"\t\tdisplayFolder: {folder}")
    lines.append(f"\t\tlineageTag: {guid()}")
    return "\n".join(lines)


def render_csv_partition(table_name, csv_file, columns) -> str:
    type_pairs = ", ".join(f'{{"{c["name"]}", {PQ_TYPE[c["type"]]}}}' for c in columns)
    m = f"""\tpartition {table_name} = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = Csv.Document(File.Contents(DataFolderPath & "{csv_file}"), [Delimiter=",", Columns={len(columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
\t\t\t\t    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{{type_pairs}}})
\t\t\t\tin
\t\t\t\t    #"Changed Type\""""
    return m


def write_table(name, csv_file, columns, calculated_columns=None, table_desc=None):
    parts = []
    if table_desc:
        parts.append(f"/// {table_desc}")
    parts.append(f"table {name}")
    parts.append(f"\tlineageTag: {guid()}")
    parts.append("")
    for c in columns:
        parts.append(render_column(
            c["name"], c["type"], c["agg"], c.get("fmt"), c.get("hidden", False),
            c.get("sort_by"), c.get("folder"), c.get("desc"),
        ))
        parts.append("")
    for cc in calculated_columns or []:
        parts.append(render_calculated_column(cc["name"], cc["dax"], cc["type"], cc["agg"], cc.get("fmt"), cc.get("desc")))
        parts.append("")
    parts.append(render_csv_partition(name, csv_file, columns))
    parts.append("")
    text = "\n".join(parts).replace("\n\n\n", "\n\n")
    (TABLES_DIR / f"{name}.tmdl").write_text(text, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Table specs: (csv column order copied exactly from generate_sample_data.py)
# ---------------------------------------------------------------------------

def col(name, type_, agg="none", **kw):
    return {"name": name, "type": type_, "agg": agg, **kw}


write_table(
    "Customers", "customers.csv",
    columns=[
        col("customer_id", "string", folder="1. Identity", desc="Unique customer identifier, e.g. CUST-0001."),
        col("customer_name", "string", folder="1. Identity"),
        col("signup_date", "dateTime", fmt="yyyy-mm-dd", folder="1. Identity"),
        col("last_active_date", "dateTime", fmt="yyyy-mm-dd", folder="1. Identity"),
        col("contract_type", "string", folder="2. Segment"),
        col("plan", "string", folder="2. Segment"),
        col("region", "string", folder="2. Segment"),
        col("tenure_months", "int64", folder="2. Segment"),
        col("monthly_revenue", "double", agg="sum", fmt="$#,##0.00", folder="3. Usage & Revenue"),
        col("usage_score", "double", fmt="0.0", folder="3. Usage & Revenue", desc="0-100 product engagement score; lower means less active."),
        col("support_tickets_90d", "int64", folder="3. Usage & Revenue"),
        col("days_since_active", "int64", folder="3. Usage & Revenue"),
        col("churn_probability", "double", fmt="0.0%", folder="4. Model Output", desc="Mock model output standing in for a trained scikit-learn/Fabric model."),
        col("churn_flag_thresholded", "int64", folder="4. Model Output"),
        col("predicted_revenue_loss", "double", agg="sum", fmt="$#,##0.00", folder="4. Model Output"),
        col("did_churn_last_month", "int64", folder="5. Backtest Ground Truth", desc="Synthetic 'what actually happened' outcome, used only to grade the mock model."),
        col("retention_call_flag", "int64", folder="5. Backtest Ground Truth", desc="Deliberately leaky demo column -- see the Data Leakage Checklist on Model Diagnostics."),
    ],
    calculated_columns=[
        {
            "name": "Risk Bucket", "type": "string", "agg": "none",
            "desc": "Buckets churn_probability into High / Medium / Low for the donut chart and slicers.",
            "dax": (
                "SWITCH(TRUE(), Customers[churn_probability] >= 0.6, \"High\", "
                "Customers[churn_probability] >= 0.3, \"Medium\", \"Low\")"
            ),
        },
        {
            "name": "Tenure Bucket", "type": "string", "agg": "none",
            "desc": "Groups tenure_months into readable ranges for the segment filters.",
            "dax": (
                "SWITCH(TRUE(), Customers[tenure_months] < 6, \"0-6 months\", "
                "Customers[tenure_months] < 12, \"6-12 months\", "
                "Customers[tenure_months] < 24, \"12-24 months\", \"24+ months\")"
            ),
        },
    ],
    table_desc="One row per customer -- the core dimension the rest of the report hangs off.",
)

write_table(
    "FeatureContributions", "feature_contributions.csv",
    columns=[
        col("customer_id", "string"),
        col("feature_name", "string"),
        col("contribution", "double", fmt="0.000"),
        col("rank", "int64"),
    ],
    table_desc="Explains each customer's churn score as 5 signed contributions (see Customer Risk Explorer).",
)

write_table(
    "RevenueHistory", "revenue_history.csv",
    columns=[
        col("customer_id", "string"),
        col("month", "dateTime", fmt="yyyy-mm-dd"),
        col("revenue", "double", agg="sum", fmt="$#,##0.00"),
    ],
    table_desc="12 months of per-customer revenue, used for the sparkline in Customer Risk Explorer.",
)

write_table(
    "MonthlyRevenue", "monthly_revenue.csv",
    columns=[
        col("month", "dateTime", fmt="yyyy-mm-dd"),
        col("actual_revenue", "double", agg="sum", fmt="$#,##0"),
        col("forecast_revenue", "double", agg="sum", fmt="$#,##0"),
        col("forecast_low", "double", agg="sum", fmt="$#,##0"),
        col("forecast_high", "double", agg="sum", fmt="$#,##0"),
        col("is_forecast_month", "int64"),
        col("mape_trend", "double", fmt="0.00", desc="Walk-forward MAPE (%) for that month; feeds the KPI sparkline."),
    ],
    table_desc="Company-level actual vs. forecast revenue -- the Overview page's headline chart.",
)

write_table(
    "CohortRetention", "cohort_retention.csv",
    columns=[
        col("signup_month", "string"),
        col("cohort_order", "int64", hidden=True),
        col("months_since_signup", "int64"),
        col("retention_rate", "double", fmt="0.0"),
        col("is_forecast", "int64"),
    ],
    table_desc="Retention curve per signup cohort, for the Overview page's cohort heatmap.",
)

write_table(
    "BacktestMetrics", "backtest_metrics.csv",
    columns=[
        col("metric_name", "string"),
        col("metric_value", "double", fmt="0.000"),
        col("metric_type", "string"),
        col("metric_display", "string"),
    ],
    table_desc="Holdout accuracy metrics (MAPE, RMSE, AUC, Precision, Recall) for Model Diagnostics.",
)

write_table(
    "Calibration", "calibration.csv",
    columns=[
        col("bucket_label", "string", sort_by="bucket_order"),
        col("predicted_avg", "double", fmt="0.0%"),
        col("actual_rate", "double", fmt="0.0%"),
        col("customer_count", "int64", agg="sum"),
        col("bucket_order", "int64", hidden=True),
    ],
    table_desc="Predicted-vs-actual churn rate per probability decile, for the calibration plot.",
)

write_table(
    "DriftMetrics", "drift_metrics.csv",
    columns=[
        col("feature_name", "string"),
        col("ks_statistic", "double", fmt="0.000"),
        col("drift_flag", "int64"),
        col("baseline_mean", "double", fmt="0.00"),
        col("recent_mean", "double", fmt="0.00"),
    ],
    table_desc="One Kolmogorov-Smirnov drift check per monitored feature.",
)

write_table(
    "DriftDistributions", "drift_distributions.csv",
    columns=[
        col("feature_name", "string"),
        col("period", "string"),
        col("bucket_label", "string", sort_by="bucket_order"),
        col("bucket_order", "int64", hidden=True),
        col("proportion", "double", fmt="0.0%"),
    ],
    table_desc="Baseline-vs-recent histograms behind the drift small multiples.",
)

write_table(
    "LeakageChecklist", "leakage_checklist.csv",
    columns=[
        col("feature_name", "string"),
        col("correlation_with_label", "double", fmt="0.000"),
        col("leakage_flag", "int64"),
        col("note", "string"),
    ],
    table_desc="Correlation of each raw feature against the real outcome, to catch potential label leakage.",
)

write_table(
    "ModelMeta", "model_meta.csv",
    columns=[
        col("last_trained_date", "dateTime", fmt="yyyy-mm-dd"),
        col("next_scheduled_retrain", "dateTime", fmt="yyyy-mm-dd"),
        col("holdout_start", "dateTime", fmt="yyyy-mm-dd"),
        col("holdout_end", "dateTime", fmt="yyyy-mm-dd"),
        col("sample_size", "int64"),
        col("holdout_mape", "double", fmt="0.00"),
        col("holdout_auc", "double", fmt="0.000"),
    ],
    table_desc="Single-row table describing the (mock) model's training run, for the retraining cadence card.",
)

# ---------------------------------------------------------------------------
# UsageDropPercent: a disconnected calculated table backing the what-if slider.
# ---------------------------------------------------------------------------

usage_drop_tag = guid()
usage_drop_text = f"""/// Disconnected slider table (0-100, step 5) behind the "usage drop %" what-if simulation.
table UsageDropPercent
\tlineageTag: {usage_drop_tag}

\tcolumn 'Usage Drop %'
\t\tdataType: int64
\t\tformatString: #,##0
\t\tlineageTag: {guid()}
\t\tsummarizeBy: none
\t\tisNameInferred
\t\tsourceColumn: [Usage Drop %]

\t\tannotation SummarizationSetBy = Automatic

\tpartition UsageDropPercent = calculated
\t\tmode: import
\t\tsource = SELECTCOLUMNS(GENERATESERIES(0, 100, 5), "Usage Drop %", [Value])
"""
(TABLES_DIR / "UsageDropPercent.tmdl").write_text(usage_drop_text, encoding="utf-8", newline="\n")

# ---------------------------------------------------------------------------
# _Measures: dedicated measures-only table (SQLBI "measure table" pattern).
# ---------------------------------------------------------------------------

MEASURES = [
    # (name, dax, format, folder, description)
    ("Next Month Revenue", 'CALCULATE(SUM(MonthlyRevenue[forecast_revenue]), MonthlyRevenue[is_forecast_month] = 1)',
     "$#,##0", "01. Forecast", "Point forecast for next month's company-wide revenue."),
    ("Forecast Low", 'CALCULATE(SUM(MonthlyRevenue[forecast_low]), MonthlyRevenue[is_forecast_month] = 1)',
     "$#,##0", "01. Forecast", "Lower bound of the 95%-style prediction interval."),
    ("Forecast High", 'CALCULATE(SUM(MonthlyRevenue[forecast_high]), MonthlyRevenue[is_forecast_month] = 1)',
     "$#,##0", "01. Forecast", "Upper bound of the 95%-style prediction interval."),
    ("Actual Revenue MTD", (
        'VAR LatestActualMonth = CALCULATE(MAX(MonthlyRevenue[month]), NOT ISBLANK(MonthlyRevenue[actual_revenue])) '
        'RETURN CALCULATE(SUM(MonthlyRevenue[actual_revenue]), MonthlyRevenue[month] = LatestActualMonth)'
    ), "$#,##0", "01. Forecast", "Actual revenue for the most recent completed month."),
    ("Forecast MAPE %", 'DIVIDE(CALCULATE(SUM(BacktestMetrics[metric_value]), BacktestMetrics[metric_name] = "Revenue MAPE"), 100)',
     "0.0%", "01. Forecast", "Walk-forward backtest MAPE for the revenue trend line."),
    ("Forecast RMSE", 'CALCULATE(SUM(BacktestMetrics[metric_value]), BacktestMetrics[metric_name] = "Revenue RMSE")',
     "$#,##0", "01. Forecast", "Walk-forward backtest RMSE for the revenue trend line."),

    ("Total Customers", "COUNTROWS(Customers)", "#,##0", "02. Churn Risk", None),
    ("High Risk Customers", 'CALCULATE(COUNTROWS(Customers), Customers[Risk Bucket] = "High")', "#,##0", "02. Churn Risk", None),
    ("Medium Risk Customers", 'CALCULATE(COUNTROWS(Customers), Customers[Risk Bucket] = "Medium")', "#,##0", "02. Churn Risk", None),
    ("Low Risk Customers", 'CALCULATE(COUNTROWS(Customers), Customers[Risk Bucket] = "Low")', "#,##0", "02. Churn Risk", None),
    ("% High Risk Customers", "DIVIDE([High Risk Customers], [Total Customers])", "0.0%", "02. Churn Risk", None),
    ("Revenue at Risk", "SUM(Customers[predicted_revenue_loss])", "$#,##0",
     "02. Churn Risk", "Expected revenue lost to churn: monthly_revenue x churn_probability, summed."),
    ("Average Churn Probability", "AVERAGE(Customers[churn_probability])", "0.0%", "02. Churn Risk", None),

    ("Usage Drop % (Selected)", 'SELECTEDVALUE(UsageDropPercent[Usage Drop %], 0)', "#,##0", "03. What-If", None),
    ("Simulated Churn Probability", (
        'VAR BaseProbability = SELECTEDVALUE(Customers[churn_probability]) '
        "VAR Bump = ([Usage Drop % (Selected)] / 100) * 0.4 "
        "RETURN IF(ISBLANK(BaseProbability), BLANK(), MIN(1, MAX(0, BaseProbability + Bump)))"
    ), "0.0%", "03. What-If", "Client-side what-if: nudges a selected customer's risk up as usage drops further."),
    ("Simulated Revenue Impact", (
        "VAR BaseRevenue = SELECTEDVALUE(Customers[monthly_revenue]) "
        "VAR BaseProbability = SELECTEDVALUE(Customers[churn_probability]) "
        "RETURN IF(ISBLANK(BaseRevenue), BLANK(), BaseRevenue * ([Simulated Churn Probability] - BaseProbability))"
    ), "$#,##0.00", "03. What-If", "Extra expected revenue at risk implied by the what-if slider."),

    ("Holdout AUC", 'CALCULATE(SUM(BacktestMetrics[metric_value]), BacktestMetrics[metric_name] = "Churn AUC")',
     "0.00", "04. Diagnostics", None),
    ("Holdout Precision", 'CALCULATE(SUM(BacktestMetrics[metric_value]), BacktestMetrics[metric_name] = "Churn Precision")',
     "0.0%", "04. Diagnostics", None),
    ("Holdout Recall", 'CALCULATE(SUM(BacktestMetrics[metric_value]), BacktestMetrics[metric_name] = "Churn Recall")',
     "0.0%", "04. Diagnostics", None),
    ("Precision at Top 10", 'CALCULATE(SUM(BacktestMetrics[metric_value]), BacktestMetrics[metric_name] = "Precision @ Top 10")',
     "0.0%", "04. Diagnostics", "Of the 10 customers we'd call first, the share who actually churned."),
    ("Drift Flag Count", "CALCULATE(COUNTROWS(DriftMetrics), DriftMetrics[drift_flag] = 1)", "#,##0", "04. Diagnostics", None),
    ("Leakage Flag Count", "CALCULATE(COUNTROWS(LeakageChecklist), LeakageChecklist[leakage_flag] = 1)", "#,##0", "04. Diagnostics", None),
    ("Last Trained Date (Text)", 'FORMAT(SELECTEDVALUE(ModelMeta[last_trained_date]), "mmmm d, yyyy")', None, "04. Diagnostics", None),
    ("Next Retrain Date (Text)", 'FORMAT(SELECTEDVALUE(ModelMeta[next_scheduled_retrain]), "mmmm d, yyyy")', None, "04. Diagnostics", None),
    ("Accuracy Note", (
        'VAR StartDate = FORMAT(SELECTEDVALUE(ModelMeta[holdout_start]), "mmm yyyy") '
        'VAR EndDate = FORMAT(SELECTEDVALUE(ModelMeta[holdout_end]), "mmm yyyy") '
        'VAR MapeText = FORMAT([Forecast MAPE %], "0.0%") '
        'VAR AucText = FORMAT([Holdout AUC], "0.00") '
        'RETURN "Model trained on data from " & StartDate & " to " & EndDate & ". Holdout MAPE = " & MapeText '
        '& ", AUC = " & AucText & ". Use predictions as decision support; validate before high-cost actions."'
    ), None, "04. Diagnostics", "The Overview page honesty note -- built from data, not hardcoded text."),
]

measures_tag = guid()
measures_parts = [f"table _Measures", f"\tlineageTag: {measures_tag}", ""]
for name, dax, fmt, folder, desc in MEASURES:
    measures_parts.append(render_measure(name, dax, fmt, folder, desc))
    measures_parts.append("")
measures_parts.append("\tcolumn Value")
measures_parts.append("\t\tisHidden")
measures_parts.append(f"\t\tlineageTag: {guid()}")
measures_parts.append("\t\tisNameInferred")
measures_parts.append("\t\tsourceColumn: [Value]")
measures_parts.append("")
measures_parts.append("\tpartition _Measures = calculated")
measures_parts.append("\t\tmode: import")
measures_parts.append("\t\tsource = {1}")
measures_parts.append("")
(TABLES_DIR / "_Measures.tmdl").write_text("\n".join(measures_parts), encoding="utf-8", newline="\n")

# ---------------------------------------------------------------------------
# relationships.tmdl
# ---------------------------------------------------------------------------

relationships_text = f"""relationship {guid()}
\tfromColumn: FeatureContributions.customer_id
\ttoColumn: Customers.customer_id

relationship {guid()}
\tfromColumn: RevenueHistory.customer_id
\ttoColumn: Customers.customer_id
"""
(MODEL_DIR / "relationships.tmdl").write_text(relationships_text, encoding="utf-8", newline="\n")

# ---------------------------------------------------------------------------
# expressions.tmdl -- the one parameter every partition reads from.
# ---------------------------------------------------------------------------

escaped_path = DATA_PATH.replace('"', '""')
expressions_text = f"""/// Folder holding the CSVs produced by data/generate_sample_data.py.
/// Change this if you move the project -- every table reads from here.
expression DataFolderPath = "{escaped_path}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
\tlineageTag: {guid()}
\tqueryGroup: Parameters

\tannotation PBI_ResultType = Text
"""
(MODEL_DIR / "expressions.tmdl").write_text(expressions_text, encoding="utf-8", newline="\n")

# ---------------------------------------------------------------------------
# database.tmdl and model.tmdl
# ---------------------------------------------------------------------------

(MODEL_DIR / "database.tmdl").write_text(
    f"database ChurnCast\n\tcompatibilityLevel: 1567\n", encoding="utf-8", newline="\n"
)

table_order = [
    "Customers", "FeatureContributions", "RevenueHistory", "MonthlyRevenue", "CohortRetention",
    "BacktestMetrics", "Calibration", "DriftMetrics", "DriftDistributions", "LeakageChecklist",
    "ModelMeta", "UsageDropPercent", "_Measures",
]
query_order = ", ".join(f'"{t}"' for t in table_order)
model_text = f"""model Model
\tculture: en-US
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tsourceQueryCulture: en-US
\tdataAccessOptions
\t\tlegacyRedirects
\t\treturnErrorValuesAsNull

queryGroup Parameters

\tannotation PBI_QueryGroupOrder = 0

annotation PBI_QueryOrder = [{query_order}]

annotation __PBI_TimeIntelligenceEnabled = 0

"""
model_text += "\n".join(f"ref table {q(t)}" for t in table_order) + "\n"
(MODEL_DIR / "model.tmdl").write_text(model_text, encoding="utf-8", newline="\n")

print("TMDL files written to", TABLES_DIR)
print("Tables:", len(list(TABLES_DIR.glob('*.tmdl'))))
