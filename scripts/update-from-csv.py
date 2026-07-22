#!/usr/bin/env python3
"""Update value.json from an EasyEquities holdings CSV export.

Usage:
    python3 scripts/update-from-csv.py /path/to/holdings.csv
    python3 scripts/update-from-csv.py /path/to/holdings.csv --value-col "Current Value"

Auto-detects the value column (headers containing 'value', 'market value',
'current value', 'zar'). If detection is wrong, pass --value-col. Amounts like
'R1 234,56' or '1,234.56' are handled.
"""
import csv, os, sys, re, argparse
import ee_common

VALUE_HINTS = ["current value", "market value", "value (zar)", "value", "zar", "amount"]


def to_number(s):
    if s is None:
        return None
    s = str(s).strip().replace("R", "").strip()
    if not s:
        return None
    s = s.replace(" ", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        return float(s)
    except ValueError:
        return None


def pick_value_col(headers, override):
    if override:
        for h in headers:
            if h.strip().lower() == override.strip().lower():
                return h
        sys.exit(f"--value-col '{override}' not found. Headers: {headers}")
    lower = {h: h.strip().lower() for h in headers}
    for hint in VALUE_HINTS:
        for h, l in lower.items():
            if l == hint:
                return h
    for hint in VALUE_HINTS:
        for h, l in lower.items():
            if hint in l:
                return h
    sys.exit(f"Could not find a value column. Headers seen: {headers}\n"
             f"Re-run with --value-col \"<exact header>\".")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--value-col", default=None)
    args = ap.parse_args()

    with open(args.csv_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("CSV has no data rows.")

    headers = list(rows[0].keys())
    vcol = pick_value_col(headers, args.value_col)

    total, n = 0.0, 0
    for row in rows:
        v = to_number(row.get(vcol))
        if v is not None:
            total += v
            n += 1

    out = ee_common.write_value(
        round(total, 2), [],
        source=f"CSV import ({os.path.basename(args.csv_path)}, {n} rows, col '{vcol}')",
    )
    print(f"Wrote value.json: {total:,.2f} from {n} rows (column '{vcol}'), "
          f"{len(out['series'])} snapshot(s).")


if __name__ == "__main__":
    main()
