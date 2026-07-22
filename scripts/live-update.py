#!/usr/bin/env python3
"""Live portfolio valuation → value.json.

Values your holdings from live market data instead of a manual total:
  stocks   -> shares x live price (Finnhub) x USD/ZAR (open.er-api)
  crypto   -> units x live coin price (CoinGecko)
  manual   -> a fixed value (for accounts without a live feed)

Reads holdings.live.json (see holdings.live.example.json). Writes value.json
via ee_common (so it also appends the daily history snapshot).

Needs a free Finnhub API key in env FINNHUB_API_KEY, or a .env file at the repo
root containing:  FINNHUB_API_KEY=xxxxx
Get one at https://finnhub.io/register (free tier covers US stock quotes).

Usage:  python3 scripts/live-update.py [--dry-run]
"""
import json, os, sys, time, urllib.request, urllib.parse
import ee_common

HOLDINGS = os.path.join(ee_common.ROOT, "holdings.live.json")
ENV_FILE = os.path.join(ee_common.ROOT, ".env")


def load_env_key():
    key = os.environ.get("FINNHUB_API_KEY")
    if key:
        return key.strip()
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE):
            line = line.strip()
            if line.startswith("FINNHUB_API_KEY=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def get_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "deskfolio/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def usd_zar():
    d = get_json("https://open.er-api.com/v6/latest/USD")
    rate = d.get("rates", {}).get("ZAR")
    if not rate:
        raise RuntimeError("Could not read USD/ZAR rate")
    return float(rate)


def finnhub_price(ticker, key):
    url = "https://finnhub.io/api/v1/quote?" + urllib.parse.urlencode({"symbol": ticker, "token": key})
    d = get_json(url)
    price = d.get("c")  # current price
    if price in (None, 0):
        raise RuntimeError(f"No price for {ticker} (got {d}). Check the ticker / key.")
    return float(price)


def coin_zar(coin_id):
    url = "https://api.coingecko.com/api/v3/simple/price?" + urllib.parse.urlencode(
        {"ids": coin_id, "vs_currencies": "zar"})
    d = get_json(url)
    return float(d[coin_id]["zar"])


def main():
    dry = "--dry-run" in sys.argv
    if not os.path.exists(HOLDINGS):
        sys.exit("No holdings.live.json. Copy holdings.live.example.json and fill in your shares.")
    cfg = json.load(open(HOLDINGS))
    key = load_env_key()

    accounts = []
    detail = []

    # Stocks: need Finnhub key.
    stock_accts = cfg.get("stocks", [])
    if stock_accts:
        if not key:
            sys.exit("FINNHUB_API_KEY not set (env or .env). Get a free key at finnhub.io/register.")
        fx = usd_zar()
        detail.append(f"USD/ZAR = {fx:.4f}")
        for acct in stock_accts:
            total = 0.0
            for h in acct.get("holdings", []):
                px = finnhub_price(h["ticker"], key)
                v = h["shares"] * px * fx
                total += v
                detail.append(f"  {h['ticker']:6s} {h['shares']:.4f} x ${px:.2f} x {fx:.2f} = R{v:.2f}")
                time.sleep(1.1)  # free tier: stay under 60 calls/min
            accounts.append({"id": acct["id"], "label": acct["label"], "value": round(total, 2)})

    # Crypto: keyless.
    for acct in cfg.get("crypto", []):
        pz = coin_zar(acct["coin"])
        v = acct["units"] * pz
        detail.append(f"  {acct['coin']} {acct['units']:.8f} x R{pz:,.0f} = R{v:.2f}")
        accounts.append({"id": acct["id"], "label": acct["label"], "value": round(v, 2)})

    # Manual: fixed values.
    for acct in cfg.get("manual", []):
        accounts.append({"id": acct["id"], "label": acct["label"], "value": round(float(acct["value"]), 2)})

    total = round(sum(a["value"] for a in accounts), 2)
    sym = cfg.get("currency_symbol", "R")

    print("\n".join(detail))
    print(f"TOTAL = {sym}{total:,.2f}")

    if dry:
        print("(dry run — value.json not written)")
        return
    ee_common.write_value(total, accounts, source="live prices (Finnhub + CoinGecko + er-api)",
                          currency_symbol=sym)
    print(f"Wrote value.json.")


if __name__ == "__main__":
    main()
