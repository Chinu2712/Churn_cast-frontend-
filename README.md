# ChurnCast — Predictive Subscription Dashboard

A custom-built web dashboard (React + Vite — **no Power BI**) showing next-month sales
forecasts and per-customer churn risk for a subscription business, built for a Microsoft-style
hackathon.

For the full reasoning behind every technical and design decision — frontend stack, UI/UX
design system, architecture diagrams, data flow — see **[TECHNICAL_APPROACH.md](./TECHNICAL_APPROACH.md)**.

For copy-pasteable setup and run commands (including Windows-specific gotchas), see
**[RUNNING.md](./RUNNING.md)**.

## What's in this repo

```
front_36/
├── TECHNICAL_APPROACH.md   # full technical write-up + diagrams (read this first)
├── data/
│   ├── generate_sample_data.py   # simulates the subscription business (pandas/numpy)
│   ├── csv_to_json.py            # stdlib-only CSV -> JSON converter (no pandas needed)
│   └── raw/                      # generated CSVs (human-inspectable)
├── frontend/                     # the dashboard itself (Vite + React)
│   ├── public/data/               # JSON files the dashboard fetches at runtime
│   └── src/                        # components, pages, hooks, styles
├── docs/
│   ├── api/                      # backend API contract (OpenAPI) for the future Java + WEKA backend
│   └── mockups/                  # early HTML/CSS/JS design mockups
└── legacy-powerbi/                # archived first draft (Power BI .pbip project) — superseded
```

## Quick start

```bash
# 1. (optional) regenerate the sample dataset
cd data
python generate_sample_data.py      # needs pandas + numpy
# if pandas isn't available in your environment, the committed CSVs already exist --
# just re-export them to JSON with the dependency-free fallback:
python csv_to_json.py

# 2. run the dashboard
cd ../frontend
npm install
npm run dev
# open http://localhost:5173
```

## Pages

| Page | URL | What it shows |
|---|---|---|
| Overview | `/` | KPI bar, forecast-vs-actual chart with prediction band, churn risk donut, cohort retention heatmap, actionable alerts table |
| Customer Risk Explorer | `/explorer` | Filterable/sortable customer table, explainability bars, what-if usage-drop slider |
| Model Diagnostics & Monitoring | `/diagnostics` | Backtest metrics, calibration plot, drift small-multiples, data leakage checklist, retrain button |
| Customer Detail (drillthrough) | `/customer/:id` | Full profile, revenue history chart, explainability for one customer |

Every page has a dark/light theme toggle (top right) that persists across navigation and page
reloads.

## Build for production

```bash
cd frontend
npm run build      # outputs frontend/dist/ — a static site, deployable anywhere
npm run preview    # sanity-check the production build locally
```

## Honesty note

All numbers in this dashboard are **synthetic** — `generate_sample_data.py` simulates a
subscription business and scores churn risk with a simple, transparent weighted formula (not a
trained ML model). This stands in for what a real Microsoft Fabric / scikit-learn pipeline would
produce; see the script's docstring and `TECHNICAL_APPROACH.md` §1/§11 for what a production
version would change.

## Connecting a real backend (Java + WEKA) in the future

There is no backend today, but the frontend is already wired to use one the moment it exists:

- **API contract:** [docs/api/openapi.yaml](./docs/api/openapi.yaml) defines every route (reads
  for customers/revenue/cohorts/model diagnostics, plus `POST /predictions/churn`,
  `POST /predictions/revenue-forecast`, and `POST /model/retrain`) with request/response shapes
  that match the existing `frontend/public/data/*.json` files exactly. See
  [docs/api/README.md](./docs/api/README.md) for the full explanation.
- **One switch to flip:** set `VITE_API_BASE_URL` in `frontend/.env` (copy from
  `frontend/.env.example`) to the backend's URL. Every chart (forecast chart, churn donut,
  calibration plot, drift monitors, the what-if slider, the retrain button) automatically starts
  reading live data and live WEKA predictions instead of the static JSON/mock formulas — no other
  code changes required.
