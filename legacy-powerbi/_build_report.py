"""
ONE-TIME SCAFFOLDING SCRIPT -- not part of the delivered project (see the
matching note in _build_tmdl.py). Generates the PBIR report definition
(pages, visuals, bookmarks) from a compact spec below, closely mirroring
confirmed real Power BI Desktop PBIR examples so the JSON is valid on
first open.
"""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).parent
REPORT_DIR = ROOT / "ChurnCast.Report"
DEF_DIR = REPORT_DIR / "definition"
PAGES_DIR = DEF_DIR / "pages"


def guid() -> str:
    return str(uuid.uuid4())


def dump(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Small helpers matching the confirmed PBIR field-reference / expr grammar
# ---------------------------------------------------------------------------

def col_field(table, column):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}}


def measure_field(table, measure):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": measure}}


def proj(field, table, name, active=None):
    p = {"field": field, "queryRef": f"{table}.{name}", "nativeQueryRef": name}
    if active is not None:
        p["active"] = active
    return p


def col_proj(table, column, active=None):
    return proj(col_field(table, column), table, column, active)


def measure_proj(table, measure, active=None):
    return proj(measure_field(table, measure), table, measure, active)


def sort_by(field, table, name, descending=True):
    return {"sort": [{"field": field, "direction": "Descending" if descending else "Ascending"}], "isDefaultSort": True}


def lit_str(v):
    return {"expr": {"Literal": {"Value": f"'{v}'"}}}


def lit_bool(v):
    return {"expr": {"Literal": {"Value": "true" if v else "false"}}}


def lit_num(v, suffix="D"):
    return {"expr": {"Literal": {"Value": f"{v}{suffix}"}}}


def container(name, x, y, w, h, visual, z=0, tab_order=0, filter_config=None, is_hidden=False):
    out = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": tab_order},
        "visual": visual,
    }
    if filter_config:
        out["filterConfig"] = filter_config
    if is_hidden:
        out["isHidden"] = True
    return out


def categorical_filter(name, table, column, values):
    """IN-list categorical filter, mirroring the confirmed tableEx.json pattern."""
    return {
        "name": name,
        "field": col_field(table, column),
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "t", "Entity": table, "Type": 0}],
            "Where": [{
                "Condition": {
                    "In": {
                        "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": column}}],
                        "Values": [[{"Literal": {"Value": f"'{v}'"}}] for v in values],
                    }
                }
            }],
        },
    }


def write_visual(page_dir, name, data):
    dump(page_dir / "visuals" / name / "visual.json", data)


# ---------------------------------------------------------------------------
# Visual-type builders (parameters kept close to the confirmed examples)
# ---------------------------------------------------------------------------

def v_textbox(text, size=28, bold=True, color="#252423"):
    return {
        "visualType": "textbox",
        "objects": {
            "general": [{"properties": {"paragraphs": [{"textRuns": [{
                "value": text,
                "textStyle": {"fontSize": f"{size}px", "fontWeight": "bold" if bold else "normal", "color": color},
            }]}]}}]
        },
        "drillFilterOtherVisuals": True,
    }


def v_card(table, measure, is_measure=True):
    field = measure_field(table, measure) if is_measure else col_field(table, measure)
    return {
        "visualType": "card",
        "query": {
            "queryState": {"Values": {"projections": [proj(field, table, measure, active=True)]}},
        },
        "drillFilterOtherVisuals": True,
    }


def v_line_chart(table, category_col, y_fields, small_multiples=None):
    y_projs = [proj(measure_field(table, m) if is_m else col_field(table, m), table, m) for (m, is_m) in y_fields]
    query_state = {
        "Category": {"projections": [col_proj(table, category_col, active=True)]},
        "Y": {"projections": y_projs},
    }
    if small_multiples:
        query_state["SmallMultiples"] = {"projections": [col_proj(small_multiples[0], small_multiples[1])]}
    return {
        "visualType": "lineChart",
        "query": {"queryState": query_state},
        "drillFilterOtherVisuals": True,
    }


def v_donut_chart(table, category_col, value_table, value_measure):
    return {
        "visualType": "donutChart",
        "query": {"queryState": {
            "Category": {"projections": [col_proj(table, category_col, active=True)]},
            "Y": {"projections": [measure_proj(value_table, value_measure)]},
        }},
        "drillFilterOtherVisuals": True,
    }


def v_bar_chart(table, category_col, y_table, y_field, y_is_measure=True, sort_desc_by_y=False):
    field = measure_field(y_table, y_field) if y_is_measure else col_field(y_table, y_field)
    query = {"queryState": {
        "Category": {"projections": [col_proj(table, category_col, active=True)]},
        "Y": {"projections": [proj(field, y_table, y_field)]},
    }}
    if sort_desc_by_y:
        query["sortDefinition"] = sort_by(field, y_table, y_field, descending=True)
    return {"visualType": "barChart", "query": query, "drillFilterOtherVisuals": True}


def v_column_chart_small_multiples(table, category_col, y_table, y_field, series_col, sm_table, sm_col):
    return {
        "visualType": "columnChart",
        "query": {"queryState": {
            "Category": {"projections": [col_proj(table, category_col, active=True)]},
            "Series": {"projections": [col_proj(table, series_col)]},
            "Y": {"projections": [measure_proj(y_table, y_field) if False else proj(col_field(y_table, y_field), y_table, y_field)]},
            "SmallMultiples": {"projections": [col_proj(sm_table, sm_col)]},
        }},
        "objects": {
            "smallMultiplesLayout": [{"properties": {
                "gridLineType": lit_str("inner"),
            }}],
        },
        "drillFilterOtherVisuals": True,
    }


def v_table(table, columns, sort_col=None, sort_desc=True, filter_cfg=None):
    projections = [col_proj(table, c) for c in columns]
    query = {"queryState": {"Values": {"projections": projections}}}
    if sort_col:
        query["sortDefinition"] = sort_by(col_field(table, sort_col), table, sort_col, descending=sort_desc)
    body = {"visualType": "tableEx", "query": query, "drillFilterOtherVisuals": True}
    return body


def v_matrix(rows_table, rows_col, columns_table, columns_col, values_table, values_col):
    return {
        "visualType": "pivotTable",
        "query": {"queryState": {
            "Rows": {"projections": [col_proj(rows_table, rows_col, active=True)]},
            "Columns": {"projections": [col_proj(columns_table, columns_col, active=True)]},
            "Values": {"projections": [{
                "field": {"Aggregation": {"Expression": col_field(values_table, values_col), "Function": 0}},
                "queryRef": f"Sum({values_table}.{values_col})",
                "nativeQueryRef": f"Average of {values_col}",
            }]},
        }},
        "objects": {
            "columnHeaders": [{"properties": {"wordWrap": lit_bool(True)}}],
        },
        "drillFilterOtherVisuals": True,
    }


def v_slicer(table, column, style="Dropdown"):
    return {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [col_proj(table, column, active=True)]}}},
        "objects": {
            "general": [{"properties": {"orientation": lit_num(0)}}],
        },
        "drillFilterOtherVisuals": True,
    }


def v_action_button(label):
    return {
        "visualType": "actionButton",
        "objects": {
            "icon": [{"properties": {"shapeType": lit_str("blank")}}],
            "text": [{"properties": {
                "show": lit_bool(True),
                "text": lit_str(label),
            }}],
            "fill": [{"properties": {"show": lit_bool(True)}},
                     {"properties": {"fillColor": {"solid": {"color": {"expr": {"ThemeDataColor": {"ColorId": 0, "Percent": 0}}}}}}, "selector": {"id": "default"}}],
            "outline": [{"properties": {"show": lit_bool(False)}}],
        },
        "drillFilterOtherVisuals": True,
    }


print("Helper library loaded OK")

# ---------------------------------------------------------------------------
# Page: Overview
# ---------------------------------------------------------------------------

PAGE_IDS = ["Overview", "CustomerRiskExplorer", "ModelDiagnostics", "CustomerDetail"]
PAGE_TITLES = {
    "Overview": "Overview",
    "CustomerRiskExplorer": "Customer Risk Explorer",
    "ModelDiagnostics": "Model Diagnostics & Monitoring",
    "CustomerDetail": "Customer Detail",
}


def build_overview():
    p = PAGES_DIR / "Overview"
    write_visual(p, "title", container("title", 24, 16, 900, 40, v_textbox("ChurnCast \u2014 Overview", size=22)))
    write_visual(p, "card_next_month_revenue", container(
        "card_next_month_revenue", 24, 72, 300, 110, v_card("_Measures", "Next Month Revenue")))
    write_visual(p, "card_actual_revenue_mtd", container(
        "card_actual_revenue_mtd", 336, 72, 300, 110, v_card("_Measures", "Actual Revenue MTD")))
    write_visual(p, "card_forecast_mape", container(
        "card_forecast_mape", 648, 72, 220, 110, v_card("_Measures", "Forecast MAPE %")))
    write_visual(p, "line_mape_trend", container(
        "line_mape_trend", 880, 72, 260, 110,
        v_line_chart("MonthlyRevenue", "month", [("mape_trend", False)])))
    write_visual(p, "card_accuracy_note", container(
        "card_accuracy_note", 1152, 72, 744, 110, v_card("_Measures", "Accuracy Note")))

    write_visual(p, "line_forecast_vs_actual", container(
        "line_forecast_vs_actual", 24, 198, 1180, 380,
        v_line_chart("MonthlyRevenue", "month", [
            ("actual_revenue", False), ("forecast_revenue", False),
            ("forecast_low", False), ("forecast_high", False),
        ])))
    write_visual(p, "donut_risk_buckets", container(
        "donut_risk_buckets", 1220, 198, 340, 380,
        v_donut_chart("Customers", "Risk Bucket", "_Measures", "Total Customers")))
    write_visual(p, "card_revenue_at_risk", container(
        "card_revenue_at_risk", 1576, 198, 320, 180, v_card("_Measures", "Revenue at Risk")))
    write_visual(p, "card_pct_high_risk", container(
        "card_pct_high_risk", 1576, 398, 320, 180, v_card("_Measures", "% High Risk Customers")))

    write_visual(p, "matrix_cohort_retention", container(
        "matrix_cohort_retention", 24, 594, 940, 460,
        v_matrix("CohortRetention", "signup_month", "CohortRetention", "months_since_signup",
                  "CohortRetention", "retention_rate")))
    write_visual(p, "table_alerts_panel", container(
        "table_alerts_panel", 980, 594, 916, 460,
        v_table("Customers",
                ["customer_name", "Risk Bucket", "churn_probability", "predicted_revenue_loss", "last_active_date"],
                sort_col="churn_probability", sort_desc=True,
                filter_cfg=None),
        filter_config={"filters": [categorical_filter("high_risk_only", "Customers", "Risk Bucket", ["High"])]}))


# ---------------------------------------------------------------------------
# Page: Customer Risk Explorer
# ---------------------------------------------------------------------------

def build_customer_risk_explorer():
    p = PAGES_DIR / "CustomerRiskExplorer"
    write_visual(p, "title", container("title", 24, 16, 900, 40, v_textbox("Customer Risk Explorer", size=22)))

    write_visual(p, "slicer_contract_type", container(
        "slicer_contract_type", 24, 72, 280, 70, v_slicer("Customers", "contract_type")))
    write_visual(p, "slicer_region", container(
        "slicer_region", 316, 72, 280, 70, v_slicer("Customers", "region")))
    write_visual(p, "slicer_plan", container(
        "slicer_plan", 608, 72, 280, 70, v_slicer("Customers", "plan")))
    write_visual(p, "slicer_tenure_bucket", container(
        "slicer_tenure_bucket", 900, 72, 280, 70, v_slicer("Customers", "Tenure Bucket")))

    write_visual(p, "table_customer_list", container(
        "table_customer_list", 24, 158, 1180, 560,
        v_table("Customers", [
            "customer_id", "customer_name", "Risk Bucket", "churn_probability",
            "tenure_months", "last_active_date", "predicted_revenue_loss",
        ], sort_col="churn_probability", sort_desc=True)))

    write_visual(p, "bar_explainability", container(
        "bar_explainability", 1220, 158, 676, 270,
        v_bar_chart("FeatureContributions", "feature_name", "FeatureContributions", "contribution",
                    y_is_measure=False, sort_desc_by_y=True)))
    write_visual(p, "text_whatif_label", container(
        "text_whatif_label", 1220, 440, 676, 30,
        v_textbox("What if usage drops further? (client-side simulation)", size=13, bold=False, color="#605E5C")))
    write_visual(p, "slicer_usage_drop", container(
        "slicer_usage_drop", 1220, 478, 676, 90, v_slicer("UsageDropPercent", "Usage Drop %")))
    write_visual(p, "card_simulated_churn_probability", container(
        "card_simulated_churn_probability", 1220, 580, 330, 138,
        v_card("_Measures", "Simulated Churn Probability")))
    write_visual(p, "card_simulated_revenue_impact", container(
        "card_simulated_revenue_impact", 1566, 580, 330, 138,
        v_card("_Measures", "Simulated Revenue Impact")))


# ---------------------------------------------------------------------------
# Page: Model Diagnostics & Monitoring
# ---------------------------------------------------------------------------

def build_model_diagnostics():
    p = PAGES_DIR / "ModelDiagnostics"
    write_visual(p, "title", container("title", 24, 16, 900, 40, v_textbox("Model Diagnostics & Monitoring", size=22)))

    write_visual(p, "card_accuracy_note", container(
        "card_accuracy_note", 24, 72, 900, 100, v_card("_Measures", "Accuracy Note")))
    write_visual(p, "card_last_trained_date", container(
        "card_last_trained_date", 940, 72, 280, 100, v_card("_Measures", "Last Trained Date (Text)")))
    write_visual(p, "card_next_retrain_date", container(
        "card_next_retrain_date", 1236, 72, 280, 100, v_card("_Measures", "Next Retrain Date (Text)")))
    write_visual(p, "button_retrain", container(
        "button_retrain", 1532, 72, 364, 100, v_action_button("Retrain Model (Fabric pipeline)")))

    write_visual(p, "table_backtest_metrics", container(
        "table_backtest_metrics", 24, 188, 460, 360,
        v_table("BacktestMetrics", ["metric_name", "metric_display", "metric_type"])))
    write_visual(p, "line_calibration", container(
        "line_calibration", 500, 188, 460, 360,
        v_line_chart("Calibration", "bucket_label", [("predicted_avg", False), ("actual_rate", False)])))
    write_visual(p, "column_drift_small_multiples", container(
        "column_drift_small_multiples", 976, 188, 920, 360,
        v_column_chart_small_multiples("DriftDistributions", "bucket_label", "DriftDistributions", "proportion",
                                        "period", "DriftDistributions", "feature_name")))

    write_visual(p, "table_drift_metrics", container(
        "table_drift_metrics", 24, 564, 690, 300,
        v_table("DriftMetrics", ["feature_name", "ks_statistic", "drift_flag", "baseline_mean", "recent_mean"])))
    write_visual(p, "table_leakage_checklist", container(
        "table_leakage_checklist", 730, 564, 1166, 300,
        v_table("LeakageChecklist", ["feature_name", "correlation_with_label", "leakage_flag", "note"])))


# ---------------------------------------------------------------------------
# Page: Customer Detail (drillthrough target, hidden from page tabs)
# ---------------------------------------------------------------------------

def build_customer_detail():
    p = PAGES_DIR / "CustomerDetail"
    write_visual(p, "title", container("title", 24, 16, 900, 40, v_textbox("Customer Detail", size=22)))
    write_visual(p, "card_customer_name", container(
        "card_customer_name", 24, 72, 400, 110, v_card("Customers", "customer_name", is_measure=False)))
    write_visual(p, "card_churn_probability", container(
        "card_churn_probability", 440, 72, 300, 110, v_card("Customers", "churn_probability", is_measure=False)))
    write_visual(p, "card_monthly_revenue", container(
        "card_monthly_revenue", 756, 72, 300, 110, v_card("Customers", "monthly_revenue", is_measure=False)))
    write_visual(p, "line_revenue_history", container(
        "line_revenue_history", 24, 198, 700, 400,
        v_line_chart("RevenueHistory", "month", [("revenue", False)])))
    write_visual(p, "bar_explainability_detail", container(
        "bar_explainability_detail", 740, 198, 700, 400,
        v_bar_chart("FeatureContributions", "feature_name", "FeatureContributions", "contribution",
                    y_is_measure=False, sort_desc_by_y=True)))


def build_page_json(page_id):
    data = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
        "name": page_id,
        "displayName": PAGE_TITLES[page_id],
        "displayOption": "FitToPage",
        "height": 1080,
        "width": 1920,
    }
    if page_id == "CustomerDetail":
        data["visibility"] = "HiddenInViewMode"
        data["filterConfig"] = {"filters": [{
            "name": "drillthrough_customer_id",
            "field": col_field("Customers", "customer_id"),
            "type": "Categorical",
            "howCreated": "User",
        }]}
    dump(PAGES_DIR / page_id / "page.json", data)


# ---------------------------------------------------------------------------
# Build everything
# ---------------------------------------------------------------------------

build_overview()
build_customer_risk_explorer()
build_model_diagnostics()
build_customer_detail()
for pid in PAGE_IDS:
    build_page_json(pid)

dump(DEF_DIR / "pages" / "pages.json", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": PAGE_IDS,
    "activePageName": "Overview",
})

dump(DEF_DIR / "version.json", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "version": "2.0.0",
})

dump(DEF_DIR / "report.json", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json",
    "themeCollection": {
        "customTheme": {
            "name": "ChurnCast-Light.json",
            "type": "RegisteredResources",
            "reportVersionAtImport": {"visual": "2.0.0", "report": "2.0.0", "page": "2.0.0"},
        },
    },
    "filterConfig": {"filters": []},
    "settings": {
        "useStylableVisualContainerHeader": True,
        "useEnhancedTooltips": True,
        "defaultDrillFilterOtherVisuals": True,
    },
    "resourcePackages": [{
        "name": "RegisteredResources",
        "type": "RegisteredResources",
        "items": [
            {"name": "ChurnCast-Light.json", "path": "ChurnCast-Light.json", "type": "CustomTheme"},
            {"name": "ChurnCast-Dark.json", "path": "ChurnCast-Dark.json", "type": "CustomTheme"},
        ],
    }],
})

# ---------------------------------------------------------------------------
# Bookmarks: Executive Summary / At-Risk Customers / Model Health
# ---------------------------------------------------------------------------

BOOKMARKS = [
    ("Executive Summary", "Overview"),
    ("At-Risk Customers", "CustomerRiskExplorer"),
    ("Model Health", "ModelDiagnostics"),
]
bookmark_ids = []
for display_name, page_id in BOOKMARKS:
    bm_id = guid()
    bookmark_ids.append(bm_id)
    dump(DEF_DIR / "bookmarks" / f"{bm_id}.bookmark.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmark/1.4.0/schema.json",
        "displayName": display_name,
        "name": bm_id,
        "options": {"targetVisualNames": [], "suppressData": True, "suppressDisplay": True},
        "explorationState": {
            "version": "1.3",
            "activeSection": page_id,
            "filters": {"byExpr": []},
        },
    })

dump(DEF_DIR / "bookmarks" / "bookmarks.json", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmarksMetadata/1.0.0/schema.json",
    "items": [{"name": bid} for bid in bookmark_ids],
})

# ---------------------------------------------------------------------------
# Report-level .platform / definition.pbir
# ---------------------------------------------------------------------------

report_logical_id = guid()
dump(REPORT_DIR / ".platform", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "Report", "displayName": "ChurnCast"},
    "config": {"version": "2.0", "logicalId": report_logical_id},
})
dump(REPORT_DIR / "definition.pbir", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0",
    "datasetReference": {"byPath": {"path": "../ChurnCast.SemanticModel"}},
})

print("Report generated:", REPORT_DIR)
print("Pages:", PAGE_IDS)
print("Bookmarks:", [b[0] for b in BOOKMARKS])

# ---------------------------------------------------------------------------
# Register both themes as StaticResources so they show up, one click apart,
# in Power BI Desktop's own Theme gallery (View > Themes). This is the real,
# supported way Power BI offers a light/dark switch -- there is no API for a
# report-embedded button to swap the whole canvas theme at view time.
# ---------------------------------------------------------------------------

import shutil

resources_dir = REPORT_DIR / "StaticResources" / "RegisteredResources"
resources_dir.mkdir(parents=True, exist_ok=True)
for theme_file in ["ChurnCast-Light.json", "ChurnCast-Dark.json"]:
    shutil.copyfile(ROOT / "themes" / theme_file, resources_dir / theme_file)
print("Registered themes:", [p.name for p in resources_dir.glob("*.json")])

