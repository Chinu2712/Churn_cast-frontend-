# Running ChurnCast

This file is the **"just tell me the commands"** guide. For *why* the project is built this
way, see [TECHNICAL_APPROACH.md](./TECHNICAL_APPROACH.md). For a tour of the pages, see
[README.md](./README.md).

> ChurnCast is a static front end (Vite + React). There is no backend server to deploy — "running
> the server" means starting Vite's local dev server, which serves the dashboard and the JSON
> data files from `frontend/public/data/`.

---

## 1. Prerequisites

| Tool | Version used in this repo | Check with |
|---|---|---|
| Node.js | v20+ (tested on v24) | `node --version` |
| npm | v10+ (tested on v11) | `npm --version` |
| Python | 3.9+ (only needed to *regenerate* data, optional) | `python --version` |

If you don't have Node.js, install it from [nodejs.org](https://nodejs.org) (LTS version).

### Windows + PowerShell gotcha

If `npm --version` fails with:

```
File ...\npm.ps1 cannot be loaded because running scripts is disabled on this system.
```

PowerShell's execution policy is blocking npm's `.ps1` wrapper. Fix it once, for your user only
(doesn't require admin rights):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Or, without changing any settings, just call the `.cmd` shim directly instead of `npm`:

```powershell
npm.cmd install
npm.cmd run dev
```

Both approaches work; the `Set-ExecutionPolicy` fix is more convenient long-term.

---

## 2. Run the dashboard (fastest path)

The sample data is already generated and committed, so you can skip straight to the dashboard:

```powershell
cd frontend
npm install        # first time only — installs React, Vite, Recharts, etc.
npm run dev
```

Vite will print a local URL, normally:

```
➜  Local:   http://localhost:5173/
```

Open that URL in your browser. The dev server supports **hot reload** — edit any file in
`frontend/src/` and the page updates instantly without a manual refresh.

Stop the server any time with `Ctrl+C` in the terminal.

---

## 3. (Optional) Regenerate the sample dataset

Only needed if you want to change the simulated business (customer count, churn rate, date
range, etc.) in `data/generate_sample_data.py`.

```powershell
cd data
python generate_sample_data.py
```

This needs `pandas` and `numpy`:

```powershell
pip install pandas numpy
```

If you'd rather not install those, the repo already has the generated CSVs in
[data/raw/](./data/raw), and you can re-export them to the JSON the dashboard reads using the
dependency-free fallback script instead:

```powershell
cd data
python csv_to_json.py
```

Both scripts write their output to `frontend/public/data/*.json`, which Vite serves as static
assets — no restart needed, just refresh the browser.

---

## 4. Build a production version

To produce an optimized, static build you could deploy to any static host (Netlify, Vercel,
GitHub Pages, Azure Static Web Apps, a plain nginx container, etc.):

```powershell
cd frontend
npm run build
```

Output goes to `frontend/dist/` — a fully self-contained folder of HTML/CSS/JS.

To sanity-check the production build locally before deploying:

```powershell
npm run preview
```

This serves `dist/` on a local port (default `http://localhost:4173`) using the same static
files a real host would serve.

---

## 5. Lint the code

```powershell
cd frontend
npm run lint
```

Runs `oxlint` (a fast Rust-based linter) over `frontend/src/`.

---

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `npm` blocked by execution policy | See §1 above — use `npm.cmd` or `Set-ExecutionPolicy`. |
| Blank page / "Failed to fetch" errors in browser console | Make sure you ran `npm run dev` from inside `frontend/`, not the repo root. |
| Port 5173 already in use | Vite will automatically try 5174, 5175, etc. — check the terminal output for the actual URL. |
| Charts show no data | Confirm `frontend/public/data/*.json` files exist; if missing, run `python csv_to_json.py` from `data/` (§3). |
| `python` not found | Try `py` instead of `python` (common on Windows installs from the Microsoft Store/python.org). |

---

## Quick reference

```powershell
# one-time setup
cd frontend
npm install

# day-to-day
npm run dev        # start dev server -> http://localhost:5173
npm run build       # production build -> frontend/dist/
npm run preview    # preview the production build
npm run lint        # lint the source
```

use npm.cmd for skipping the shim policy
