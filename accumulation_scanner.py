"""
accumulation_scanner.py
------------------------
The brain of the bot. For every token in config.SECTORS, checks whether it
looks like it's leaving an accumulation/consolidation phase, and returns a
scored signal. Binance tokens get a full technical read (BBW contraction,
volume spike, EMA reclaim, RSI cross, range breakout). DexScreener tokens
get a lighter liquidity/volume-acceleration read, since free DEX APIs don't
expose historical candles.
"""

import time

import config
import indicators
from binance_client import get_klines
from coingecko_client import get_contract_addresses, get_market_data, get_trending_ids
from dexscreener_client import get_best_pair_for_token_address, get_pair_data
from state import get_dex_history, set_dex_history


def analyze_binance_token(symbol: str, binance_symbol: str, timeframe: str):
    raw_candles = get_klines(binance_symbol, timeframe, limit=config.LOOKBACK_CANDLES + 30)
    if not raw_candles:
        return None

    # Binance returns the currently-forming (not yet closed) candle as the
    # last element. Scoring that live/incomplete candle is exactly what
    # causes "big spike then it reverses" false alerts - we'd be reacting to
    # a move mid-candle before it's had a chance to actually finish and
    # possibly retrace. Drop it; only ever score fully closed candles.
    candles = raw_candles[:-1]
    if len(candles) < config.LOOKBACK_CANDLES:
        return None

    close_vals = indicators.closes(candles)
    ema_vals = indicators.ema(close_vals, config.EMA_PERIOD)
    rsi_vals = indicators.rsi(close_vals, config.RSI_PERIOD)
    bbw_vals = indicators.bollinger_band_width(close_vals, period=20)

    last_close = close_vals[-1]
    prev_close = close_vals[-2]
    last_ema = ema_vals[-1]
    prev_ema = ema_vals[-2]
    last_rsi = rsi_vals[-1]
    prev_rsi = rsi_vals[-2]
    last_bbw = bbw_vals[-1]

    reasons = []
    score = 0

    # 1. Was the token coiled recently? (BBW hit a relative low in lookback window)
    recent_bbw_window = bbw_vals[-config.LOOKBACK_CANDLES:]
    bbw_percentile = indicators.percentile_rank(recent_bbw_window, last_bbw)
    was_coiled = any(
        indicators.percentile_rank(recent_bbw_window, w) <= config.BBW_CONTRACTION_PERCENTILE
        for w in recent_bbw_window[-8:] if w is not None
    )
    if was_coiled:
        score += 25
        reasons.append("volatility contraction (range squeeze) detected recently")

    # 2. Volume spike on latest closed candle
    avg_vol = indicators.avg_volume(candles[:-1], config.LOOKBACK_CANDLES)
    last_vol = candles[-1]["volume"]
    vol_ratio = (last_vol / avg_vol) if avg_vol else 0
    if vol_ratio >= config.VOLUME_SPIKE_MULTIPLIER:
        score += 25
        reasons.append(f"volume spike {vol_ratio:.1f}x average")

    # 3. Range breakout - close above recent range high, AND the candle must
    # have actually closed strong (near its own high), not spike up on a
    # wick and get rejected back down within the same candle. A close deep
    # in the lower part of the candle's own range, even if technically above
    # the prior range high, is a rejection signature, not a real breakout.
    range_high, range_low = indicators.range_high_low(candles, config.LOOKBACK_CANDLES)
    last_candle = candles[-1]
    candle_range = last_candle["high"] - last_candle["low"]
    close_strength = ((last_candle["close"] - last_candle["low"]) / candle_range) if candle_range else 1.0
    broke_range = (
        range_high is not None and last_close > range_high and close_strength >= 0.6
    )
    if broke_range:
        score += 20
        reasons.append(f"closed above {config.LOOKBACK_CANDLES}-candle range high (closed strong, not a rejected wick)")

    # 4. EMA reclaim - crossed above EMA from below
    ema_reclaim = (
        last_ema is not None and prev_ema is not None
        and prev_close <= prev_ema and last_close > last_ema
    )
    if ema_reclaim:
        score += 15
        reasons.append(f"reclaimed EMA{config.EMA_PERIOD}")

    # 5. RSI momentum cross
    rsi_cross = (
        last_rsi is not None and prev_rsi is not None
        and prev_rsi <= config.RSI_BREAKOUT_LEVEL and last_rsi > config.RSI_BREAKOUT_LEVEL
    )
    if rsi_cross:
        score += 15
        reasons.append(f"RSI crossed above {config.RSI_BREAKOUT_LEVEL}")

    higher_lows = indicators.is_higher_low_structure(candles, config.LOOKBACK_CANDLES)
    if higher_lows:
        reasons.append("higher-low structure inside the range")

    return {
        "symbol": symbol,
        "source": "binance",
        "timeframe": timeframe,
        "score": score,
        "reasons": reasons,
        "last_price": last_close,
        "bbw_percentile": round(bbw_percentile, 1),
        "volume_ratio": round(vol_ratio, 2),
        "higher_lows": higher_lows,
    }


def _score_dex_snapshot(snap: dict, state_key: str):
    """
    Shared scoring logic for any DEX snapshot, whether it came from a
    hand-provided pair address or from auto-discovery via a verified
    contract address. Returns (score, reasons, liq_growth_pct, vol_accel).
    """
    prev = get_dex_history(state_key)
    set_dex_history(state_key, {**snap, "ts": time.time()})

    reasons = []
    score = 0

    # Liquidity growth vs last scan (proxy for real capital entering, not just wash volume)
    liq_growth_pct = None
    if prev and prev.get("liquidity_usd"):
        liq_growth_pct = (snap["liquidity_usd"] - prev["liquidity_usd"]) / prev["liquidity_usd"] * 100
        if liq_growth_pct >= config.DEX_LIQUIDITY_GROWTH_THRESHOLD_PCT:
            score += 30
            reasons.append(f"liquidity up {liq_growth_pct:.1f}% since last scan")

    # Volume acceleration: h1 run-rate vs h24 average run-rate
    h1 = snap["volume_h1"]
    h24_avg_hourly = snap["volume_h24"] / 24 if snap["volume_h24"] else 0
    vol_accel = (h1 / h24_avg_hourly) if h24_avg_hourly else 0
    if vol_accel >= config.VOLUME_SPIKE_MULTIPLIER:
        score += 30
        reasons.append(f"1h volume running {vol_accel:.1f}x the 24h average pace")

    # Buy/sell pressure
    buys, sells = snap["txns_h1_buys"], snap["txns_h1_sells"]
    total_txns = buys + sells
    buy_ratio = (buys / total_txns) if total_txns else 0.5
    if total_txns >= 20 and buy_ratio >= 0.6:
        score += 20
        reasons.append(f"buy-side pressure ({buys} buys vs {sells} sells in 1h)")

    # Positive but not already fully extended momentum
    if 3 <= snap["price_change_h1"] <= 60:
        score += 20
        reasons.append(f"price up {snap['price_change_h1']:.1f}% in 1h (early-stage move)")

    return score, reasons, liq_growth_pct, vol_accel


def analyze_dex_token(symbol: str, chain: str, pair_address: str):
    """For tokens where you've hand-provided an exact pair/pool address."""
    snap = get_pair_data(chain, pair_address)
    if snap is None:
        return None

    state_key = f"{chain}:{pair_address}"
    score, reasons, liq_growth_pct, vol_accel = _score_dex_snapshot(snap, state_key)

    return {
        "symbol": symbol,
        "source": "dexscreener",
        "timeframe": "n/a",
        "score": score,
        "reasons": reasons,
        "last_price": snap["price_usd"],
        "liquidity_usd": snap["liquidity_usd"],
        "liquidity_growth_pct": liq_growth_pct,
        "volume_accel": round(vol_accel, 2),
    }


def analyze_dexscreener_auto_token(symbol: str, coingecko_id: str):
    """
    For tokens with no hand-provided pair address. Looks up the token's
    VERIFIED contract address(es) via CoinGecko, then asks DexScreener for
    every pool trading that exact address and picks the highest-liquidity
    one automatically - no guessed/scam-risk pair address involved.
    Returns None if the token has no on-chain contract CoinGecko knows about,
    or no DEX pools were found for it.
    """
    if not coingecko_id:
        return None

    addresses = get_contract_addresses(coingecko_id)
    if not addresses:
        return None

    best_overall = None
    for addr in addresses:
        found = get_best_pair_for_token_address(addr)
        if found:
            chain, pair_address, snap = found
            if snap and (best_overall is None or snap["liquidity_usd"] > best_overall[2]["liquidity_usd"]):
                best_overall = (chain, pair_address, snap)

    if not best_overall:
        return None

    chain, pair_address, snap = best_overall
    state_key = f"{chain}:{pair_address}"
    score, reasons, liq_growth_pct, vol_accel = _score_dex_snapshot(snap, state_key)

    return {
        "symbol": symbol,
        "source": f"dexscreener-auto ({chain})",
        "timeframe": "n/a",
        "score": score,
        "reasons": reasons,
        "last_price": snap["price_usd"],
        "liquidity_usd": snap["liquidity_usd"],
        "liquidity_growth_pct": liq_growth_pct,
        "volume_accel": round(vol_accel, 2),
    }


def analyze_coingecko_only_token(symbol: str, coingecko_id: str):
    """
    For tokens with no reliable exchange source (not on Binance, no known DEX
    pair). No technical/candle-based score - this token can only ever alert
    via the trending bonus (applied later in scan_all_sectors), i.e. "this
    thing is suddenly getting searched a lot." Fundamentals get attached
    later too. Returns a bare-bones result now; enrich_with_fundamentals()
    fills in the rest.
    """
    return {
        "symbol": symbol,
        "source": "coingecko_only",
        "timeframe": "n/a",
        "score": 0,
        "reasons": [],
        "last_price": None,
    }


def enrich_with_fundamentals(results, market_data, trending_ids, sector_id_lookup):
    """
    Mutates each result in-place: attaches market cap / FDV, adds the
    trending bonus to the score if applicable, and flags a low-float
    warning when FDV dwarfs market cap. Cheap - uses data already fetched
    in 2 bulk API calls, no extra network calls per token.
    """
    for res in results:
        cg_id = sector_id_lookup.get((res["sector"], res["symbol"]))
        if not cg_id:
            continue

        data = market_data.get(cg_id)
        if data:
            res["market_cap"] = data.get("market_cap")
            res["fdv"] = data.get("fdv")
            res["price_change_24h"] = data.get("price_change_24h")
            if res.get("last_price") is None:
                res["last_price"] = data.get("price")

            mc, fdv = data.get("market_cap"), data.get("fdv")
            if mc and fdv and mc > 0 and fdv / mc >= config.FDV_MCAP_WARNING_RATIO:
                res["low_float_warning"] = f"FDV is {fdv / mc:.1f}x market cap (heavy future dilution)"

        if cg_id in trending_ids:
            res["score"] += config.TRENDING_BONUS_POINTS
            res["reasons"].append("trending on CoinGecko right now (social attention spike)")



def scan_all_sectors():
    """Runs the full scan across every sector/token/timeframe. Returns a
    flat list of result dicts (including ones that scored below threshold -
    caller decides what to do with them)."""
    results = []
    sector_id_lookup = {}  # (sector, symbol) -> coingecko_id, used for the fundamentals merge below

    for sector, tokens in config.SECTORS.items():
        for token in tokens:
            sector_id_lookup[(sector, token["symbol"])] = token.get("coingecko_id")
            got_technical_result = False

            if token["source"] == "binance":
                for tf in config.TIMEFRAMES:
                    res = analyze_binance_token(token["symbol"], token["binance_symbol"], tf)
                    if res:
                        res["sector"] = sector
                        results.append(res)
                        got_technical_result = True
            elif token["source"] == "dexscreener":
                res = analyze_dex_token(token["symbol"], token["dex_chain"], token["dex_pair"])
                if res:
                    res["sector"] = sector
                    results.append(res)
                    got_technical_result = True
            elif token["source"] == "coingecko_only":
                res = analyze_coingecko_only_token(token["symbol"], token.get("coingecko_id"))
                res["sector"] = sector
                results.append(res)
                got_technical_result = True

            # If a binance/dexscreener token couldn't be fetched (wrong symbol,
            # not listed, etc), still give it a fundamentals-only fallback row
            # so it isn't silently dropped - it can still alert via the
            # trending bonus, and you'll see it in the scan log either way.
            if not got_technical_result:
                res = analyze_coingecko_only_token(token["symbol"], token.get("coingecko_id"))
                res["sector"] = sector
                res["source"] = f"{token['source']} (fetch failed - fundamentals only)"
                results.append(res)

    if config.COINGECKO_ENABLED:
        all_ids = [tid for tid in sector_id_lookup.values() if tid]
        market_data = get_market_data(all_ids)
        trending_ids = get_trending_ids()
        enrich_with_fundamentals(results, market_data, trending_ids, sector_id_lookup)

    return results

