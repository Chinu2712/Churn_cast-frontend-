"""
csv_to_json.py
===============

Pure standard-library fallback for turning data/raw/*.csv into the JSON
files the React dashboard fetches (frontend/public/data/*.json).

WHY THIS EXISTS SEPARATELY FROM generate_sample_data.py
---------------------------------------------------------
generate_sample_data.py uses pandas/numpy to *compute* the sample data (the
churn formula, the revenue forecast trend line, the drift statistics, etc.)
and, if pandas is available, it writes both CSV and JSON directly.

Some machines occasionally have a broken or policy-blocked pandas install
(for example a native-code security scanner interfering with pandas' many
compiled .pyx extensions) even though the CSVs it previously wrote are
still sitting on disk and perfectly valid. This script has zero third-party
dependencies -- just csv + json from the standard library -- so it always
works as a "re-export the data I already generated" escape hatch.

Usage:
    python csv_to_json.py
"""

import csv
import json
from pathlib import Path

RAW_DIR = Path(__file__).parent / "raw"
JSON_OUTPUT_DIR = Path(__file__).parent.parent / "frontend" / "public" / "data"


def coerce(value: str):
    """Turn a CSV string cell into an int, float, or plain string -- in that
    order of preference, falling back to the original string. This mirrors
    what pandas' read_csv/to_json would have inferred, without needing
    pandas to do it."""
    if value == "":
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def convert_file(csv_path: Path, json_path: Path) -> int:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [{key: coerce(value) for key, value in row.items()} for row in reader]
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return len(rows)


def main() -> None:
    JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_files = sorted(RAW_DIR.glob("*.csv"))
    if not csv_files:
        raise SystemExit(f"No CSV files found in {RAW_DIR}. Run generate_sample_data.py first.")

    for csv_path in csv_files:
        json_path = JSON_OUTPUT_DIR / f"{csv_path.stem}.json"
        count = convert_file(csv_path, json_path)
        print(f"{csv_path.name:28s} -> {json_path.name:28s} ({count} rows)")

    print(f"\nWrote {len(csv_files)} JSON files to {JSON_OUTPUT_DIR}")


if __name__ == "__main__":
    main()
