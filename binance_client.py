"""
binance_client.py
------------------
Thin wrapper around Binance's public REST API (no API key needed for klines).
"""

import requests

BASE_URL = "https://api.binance.com"


def get_klines(symbol: str, interval: str, limit: int = 100):
    """
    Fetch candlestick data for a Binance spot symbol.

    Returns a list of dicts (oldest -> newest), each with:
      open_time, open, high, low, close, volume, close_time
    Returns None on error (bad symbol, network issue, etc.) - caller should
    handle that gracefully rather than crashing the whole scan loop.
    """
    url = f"{BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        raw = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"[binance_client] Error fetching {symbol} {interval}: {e}")
        return None

    candles = []
    for row in raw:
        candles.append({
            "open_time": row[0],
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
            "close_time": row[6],
        })
    return candles
