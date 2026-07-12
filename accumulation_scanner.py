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
from dexscreener_client import get_pair_data
from state import get_dex_history, set_dex_history


def analyze_binance_token(symbol: str, binance_symbol: str, timeframe: str):
    candles = get_klines(binance_symbol, timeframe, limit=config.LOOKBACK_CANDLES + 30)
    if not candles or len(candles) < config.LOOKBACK_CANDLES:
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

    # 3. Range breakout - close above recent range high
    range_high, range_low = indicators.range_high_low(candles, config.LOOKBACK_CANDLES)
    broke_range = range_high is not None and last_close > range_high
    if broke_range:
        score += 20
        reasons.append(f"closed above {config.LOOKBACK_CANDLES}-candle range high")

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


def analyze_dex_token(symbol: str, chain: str, pair_address: str):
    snap = get_pair_data(chain, pair_address)
    if snap is None:
        return None

    key = f"{chain}:{pair_address}"
    prev = get_dex_history(key)
    set_dex_history(key, {**snap, "ts": time.time()})

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


def scan_all_sectors():
    """Runs the full scan across every sector/token/timeframe. Returns a
    flat list of result dicts (including ones that scored below threshold -
    caller decides what to do with them)."""
    results = []

    for sector, tokens in config.SECTORS.items():
        for token in tokens:
            if token["source"] == "binance":
                for tf in config.TIMEFRAMES:
                    res = analyze_binance_token(token["symbol"], token["binance_symbol"], tf)
                    if res:
                        res["sector"] = sector
                        results.append(res)
            elif token["source"] == "dexscreener":
                res = analyze_dex_token(token["symbol"], token["dex_chain"], token["dex_pair"])
                if res:
                    res["sector"] = sector
                    results.append(res)

    return results
