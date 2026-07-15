"""
dexscreener_client.py
----------------------
Wrapper around the free DexScreener public API. No key required.

DexScreener does NOT give raw OHLCV candles on the free API - only current
pair stats (price, volume over rolling windows, liquidity, price change %).
So for DEX tokens we can't compute Bollinger Bands / RSI the same way we do
for Binance. Instead we use a lighter-weight liquidity + volume-acceleration
check, which is arguably more relevant for pump.fun-style shitcoins anyway.
"""

import requests

BASE_URL = "https://api.dexscreener.com/latest/dex/pairs"
TOKENS_URL = "https://api.dexscreener.com/latest/dex/tokens"


def get_pair_data(chain: str, pair_address: str):
    """
    Fetch current stats for a DEX pair, given an exact pair/pool address.

    Returns a dict with: price_usd, liquidity_usd, volume_h1, volume_h24,
    price_change_h1, price_change_m5, txns_h1_buys, txns_h1_sells.
    Returns None on error.
    """
    url = f"{BASE_URL}/{chain}/{pair_address}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"[dexscreener_client] Error fetching {chain}/{pair_address}: {e}", flush=True)
        return None

    pair = data.get("pair") or (data.get("pairs") or [None])[0]
    if not pair:
        print(f"[dexscreener_client] No pair data returned for {chain}/{pair_address}", flush=True)
        return None

    return _normalize_pair(pair)


def get_best_pair_for_token_address(token_address: str):
    """
    Given a token's VERIFIED contract address (get this from CoinGecko, not
    from search - search results for DEX pairs are full of scam tokens that
    impersonate real tickers with fake mirrored prices), finds every pool
    that token trades on across every chain, and returns the one with the
    highest liquidity. This avoids ever hand-picking/guessing a pair address.

    Returns (chain, pair_address, snapshot_dict) or None if nothing found.
    """
    url = f"{TOKENS_URL}/{token_address}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"[dexscreener_client] Error looking up token {token_address}: {e}", flush=True)
        return None

    pairs = data.get("pairs") or []
    if not pairs:
        return None

    best = max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd", 0) or 0)
    chain = best.get("chainId")
    pair_address = best.get("pairAddress")
    if not chain or not pair_address:
        return None

    return chain, pair_address, _normalize_pair(best)


def _normalize_pair(pair):
    try:
        return {
            "price_usd": float(pair.get("priceUsd", 0) or 0),
            "liquidity_usd": float((pair.get("liquidity") or {}).get("usd", 0) or 0),
            "volume_h1": float((pair.get("volume") or {}).get("h1", 0) or 0),
            "volume_h24": float((pair.get("volume") or {}).get("h24", 0) or 0),
            "price_change_h1": float((pair.get("priceChange") or {}).get("h1", 0) or 0),
            "price_change_m5": float((pair.get("priceChange") or {}).get("m5", 0) or 0),
            "txns_h1_buys": int(((pair.get("txns") or {}).get("h1") or {}).get("buys", 0) or 0),
            "txns_h1_sells": int(((pair.get("txns") or {}).get("h1") or {}).get("sells", 0) or 0),
        }
    except (TypeError, ValueError) as e:
        print(f"[dexscreener_client] Malformed pair data: {e}", flush=True)
        return None

