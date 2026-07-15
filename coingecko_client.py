"""
coingecko_client.py
---------------------
Free, keyless CoinGecko public API access - no signup, no key needed.
Used for two things:
  1. Fundamentals: market cap + FDV (fully diluted valuation) for your whole
     watchlist in a SINGLE bulk API call.
  2. Trending: which coins people are actively searching for right now on
     CoinGecko - the closest free, honest proxy for "social buzz" (real
     Twitter/X sentiment APIs are all paywalled as of 2026).

Both calls together = 2 requests per scan, regardless of how many tokens
you're tracking - comfortably within the free public rate limit (5-15
calls/min) even scanning every 15 minutes.
"""

import requests

BASE_URL = "https://api.coingecko.com/api/v3"


def get_market_data(coingecko_ids):
    """
    Bulk-fetch market cap / FDV / volume / 24h change for a list of
    CoinGecko ids in ONE request.

    Returns a dict: {coingecko_id: {market_cap, fdv, volume_24h, price_change_24h}}
    Ids CoinGecko doesn't recognize are just absent from the result - no error.
    Returns {} on total failure (network issue etc).
    """
    ids = [i for i in coingecko_ids if i]
    if not ids:
        return {}

    url = f"{BASE_URL}/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(ids),
        "price_change_percentage": "24h",
        "per_page": 250,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        raw = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"[coingecko_client] Error fetching market data: {e}", flush=True)
        return {}

    result = {}
    for coin in raw:
        result[coin["id"]] = {
            "price": coin.get("current_price"),
            "market_cap": coin.get("market_cap"),
            "fdv": coin.get("fully_diluted_valuation"),
            "volume_24h": coin.get("total_volume"),
            "price_change_24h": coin.get("price_change_percentage_24h"),
        }
    return result


def get_contract_addresses(coingecko_id: str):
    """
    Returns a list of VERIFIED contract addresses for this token across every
    chain CoinGecko has it listed on (their team/community verifies these -
    far more trustworthy than trusting whatever a DexScreener search surfaces,
    which is often full of scam tokens impersonating a real ticker with a
    mirrored fake price).

    Returns [] on failure or if the token has no on-chain contract (e.g. it's
    a native L1 asset like a Cosmos coin with no ERC-20-style address).
    """
    url = f"{BASE_URL}/coins/{coingecko_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "false",
        "community_data": "false",
        "developer_data": "false",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"[coingecko_client] Error fetching contract addresses for {coingecko_id}: {e}", flush=True)
        return []

    platforms = data.get("platforms") or {}
    return [addr for addr in platforms.values() if addr]


def get_trending_ids():
    """
    Returns a set of CoinGecko ids currently on the trending list (top
    searched coins in the last 24h - CoinGecko's free social-attention signal).
    Returns an empty set on failure.
    """
    url = f"{BASE_URL}/search/trending"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        raw = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"[coingecko_client] Error fetching trending list: {e}", flush=True)
        return set()

    ids = set()
    for item in raw.get("coins", []):
        coin_id = (item.get("item") or {}).get("id")
        if coin_id:
            ids.add(coin_id)
    return ids
