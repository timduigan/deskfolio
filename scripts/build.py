#!/usr/bin/env python3
"""Build value.json from holdings.json (the manual data source).

holdings.json shape:
  { "currency": "ZAR",
    "accounts": [ { "id": "usd", "label": "USD account", "value": 9980 }, ... ] }

Sums the accounts into a total, appends a dated snapshot to history.json, and
writes value.json (with the derived daily P/L and chart series).

Usage:  python3 scripts/build.py
"""
import json, os, sys
import ee_common

HOLDINGS = os.path.join(ee_common.ROOT, "holdings.json")


def main():
    if not os.path.exists(HOLDINGS):
        sys.exit("No holdings.json found. Copy holdings.example.json to holdings.json "
                 "and fill in your account values, then re-run.")
    with open(HOLDINGS) as f:
        h = json.load(f)

    accounts = [
        {"id": a.get("id"), "label": a.get("label", a.get("id", "")),
         "value": round(float(a.get("value", 0) or 0), 2)}
        for a in h.get("accounts", [])
    ]
    total = round(sum(a["value"] for a in accounts), 2)

    # Currency symbol comes from config.json if present, else default R.
    sym = "R"
    cfg = os.path.join(ee_common.ROOT, "config.json")
    if os.path.exists(cfg):
        try:
            sym = json.load(open(cfg)).get("currency_symbol", "R")
        except (ValueError, OSError):
            pass

    out = ee_common.write_value(total, accounts, source="manual (holdings.json)",
                                currency_symbol=sym)
    print(f"Wrote value.json: {sym}{total:,.2f} as of {out['as_of']} "
          f"({len(out['series'])} snapshot(s), {len(accounts)} accounts)")


if __name__ == "__main__":
    main()
