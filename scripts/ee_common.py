"""Shared data logic for the EasyEquities widget.

Owns the two data files the widget revolves around (both at the repo root):
  history.json  — append-only daily snapshots [{date, total}, ...]
  value.json    — what the widget reads: total, day P/L, chart series, accounts

Paths resolve relative to this file, so the repo works wherever it's cloned.
"""
import json, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY = os.path.join(ROOT, "history.json")
VALUE = os.path.join(ROOT, "value.json")


def load_history():
    if os.path.exists(HISTORY):
        try:
            with open(HISTORY) as f:
                return json.load(f)
        except (ValueError, OSError):
            return []
    return []


def upsert_history(total, date):
    """Replace today's snapshot if present, else append. Keeps history sorted."""
    hist = load_history()
    for e in hist:
        if e.get("date") == date:
            e["total"] = round(total, 2)
            break
    else:
        hist.append({"date": date, "total": round(total, 2)})
    hist.sort(key=lambda e: e.get("date", ""))
    with open(HISTORY, "w") as f:
        json.dump(hist, f, indent=2)
    return hist


def write_value(total, accounts, source, currency_symbol="R", date=None, max_points=365):
    """Write value.json. `accounts` is a list of {id,label,value} (may be empty)."""
    date = date or datetime.date.today().isoformat()
    hist = upsert_history(total, date)

    day_change = day_change_pct = None
    if len(hist) >= 2:
        prev = hist[-2]["total"]
        day_change = round(total - prev, 2)
        if prev:
            day_change_pct = round((total - prev) / prev * 100, 2)

    series = [{"date": e["date"], "value": e["total"]} for e in hist[-max_points:]]
    out = {
        "total": round(total, 2),
        "currency_symbol": currency_symbol,
        "as_of": date,
        "source": source,
        "day_change": day_change,
        "day_change_pct": day_change_pct,
        "accounts": accounts,
        "series": series,
    }
    with open(VALUE, "w") as f:
        json.dump(out, f, indent=2)
    return out
