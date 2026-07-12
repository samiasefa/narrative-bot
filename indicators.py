"""
indicators.py
-------------
Pure-python indicator math (no TA-lib dependency). Works on a list of
candle dicts as returned by binance_client.get_klines().
"""

from statistics import mean, stdev


def closes(candles):
    return [c["close"] for c in candles]


def volumes(candles):
    return [c["volume"] for c in candles]


def ema(values, period):
    """Returns a list of EMA values, same length as input (first period-1
    values are None since EMA needs a seed)."""
    if len(values) < period:
        return [None] * len(values)

    k = 2 / (period + 1)
    result = [None] * (period - 1)
    seed = mean(values[:period])
    result.append(seed)
    prev = seed
    for v in values[period:]:
        cur = v * k + prev * (1 - k)
        result.append(cur)
        prev = cur
    return result


def rsi(values, period=14):
    """Standard Wilder's RSI. Returns list same length as input, leading
    entries None until enough data."""
    if len(values) < period + 1:
        return [None] * len(values)

    gains, losses = [], []
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    result = [None] * period
    avg_gain = mean(gains[:period])
    avg_loss = mean(losses[:period])

    def calc_rsi(ag, al):
        if al == 0:
            return 100.0
        rs = ag / al
        return 100 - (100 / (1 + rs))

    result.append(calc_rsi(avg_gain, avg_loss))

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        result.append(calc_rsi(avg_gain, avg_loss))

    return result


def bollinger_band_width(values, period=20, num_std=2):
    """Returns list of BB width (as % of the middle band) same length as
    input, leading entries None until enough data."""
    result = [None] * (period - 1)
    for i in range(period - 1, len(values)):
        window = values[i - period + 1: i + 1]
        mid = mean(window)
        sd = stdev(window) if len(window) > 1 else 0
        upper = mid + num_std * sd
        lower = mid - num_std * sd
        width_pct = ((upper - lower) / mid * 100) if mid else 0
        result.append(width_pct)
    return result


def percentile_rank(values, target):
    """What percentile is `target` at, relative to `values` (ignoring Nones)?
    Returns 0-100."""
    clean = [v for v in values if v is not None]
    if not clean:
        return 50.0
    below_or_equal = sum(1 for v in clean if v <= target)
    return (below_or_equal / len(clean)) * 100


def avg_volume(candles, lookback):
    vols = volumes(candles)[-lookback:]
    return mean(vols) if vols else 0


def range_high_low(candles, lookback, exclude_last=True):
    """Highest high / lowest low over the last `lookback` candles, excluding
    the most recent (in-progress / just-closed) candle if exclude_last."""
    window = candles[-lookback - 1:-1] if exclude_last else candles[-lookback:]
    if not window:
        return None, None
    highs = [c["high"] for c in window]
    lows = [c["low"] for c in window]
    return max(highs), min(lows)


def is_higher_low_structure(candles, lookback):
    """Very simple check: split the lookback window into thirds and check
    that the lowest low of each third is not lower than the previous third's
    lowest low - i.e. rough 'stepping up' rather than pure downtrend/chop."""
    window = candles[-lookback:]
    if len(window) < 9:
        return False
    third = len(window) // 3
    seg1 = window[:third]
    seg2 = window[third:2 * third]
    seg3 = window[2 * third:]
    low1 = min(c["low"] for c in seg1)
    low2 = min(c["low"] for c in seg2)
    low3 = min(c["low"] for c in seg3)
    return low2 >= low1 * 0.98 and low3 >= low2 * 0.98
