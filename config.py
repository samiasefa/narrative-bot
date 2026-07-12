"""
config.py
---------
Central place to edit: sectors/tokens you track, timeframes, and detection thresholds.
Nothing in here should require touching other files.
"""

import os

# ---------------------------------------------------------------------------
# TELEGRAM (fill these in, or set as environment variables of the same name)
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "PUT_YOUR_CHAT_ID_HERE")

# ---------------------------------------------------------------------------
# TIMEFRAMES
# ---------------------------------------------------------------------------
# Binance kline intervals to scan. Your bot logic looks at both and requires
# agreement (or at least no conflict) between them before alerting.
TIMEFRAMES = ["5m", "15m"]

# How often the whole scan loop runs, in seconds. 5m timeframe -> no point
# checking more often than every ~60-90s (rate limits + candle close timing).
SCAN_INTERVAL_SECONDS = 90

# ---------------------------------------------------------------------------
# SECTORS / TOKENS
# ---------------------------------------------------------------------------
# Each token entry:
#   symbol      -> display name
#   source      -> "binance" or "dexscreener"
#   binance_symbol -> required if source == "binance" (must be a real Binance pair)
#   dex_chain   -> required if source == "dexscreener", e.g. "solana", "ethereum", "base"
#   dex_pair    -> required if source == "dexscreener", the pair/pool address on DexScreener
#
# NOTE: For true low-cap memecoins there is no fixed list that stays relevant -
# you MUST edit dex_pair addresses yourself as tokens rotate. Get the pair
# address from dexscreener.com (it's in the URL of the token's page, NOT the
# token's own contract address - it's the pool/pair address).

SECTORS = {
    "RWA": [
        {"symbol": "ONDO", "source": "binance", "binance_symbol": "ONDOUSDT"},
        {"symbol": "POLYX", "source": "binance", "binance_symbol": "POLYXUSDT"},
        {"symbol": "TRU", "source": "binance", "binance_symbol": "TRUUSDT"},
        {"symbol": "CFG", "source": "binance", "binance_symbol": "CFGUSDT"},
    ],
    "AI": [
        {"symbol": "FET", "source": "binance", "binance_symbol": "FETUSDT"},
        {"symbol": "RENDER", "source": "binance", "binance_symbol": "RENDERUSDT"},
        {"symbol": "TAO", "source": "binance", "binance_symbol": "TAOUSDT"},
        {"symbol": "WLD", "source": "binance", "binance_symbol": "WLDUSDT"},
    ],
    "DePIN": [
        {"symbol": "HNT", "source": "binance", "binance_symbol": "HNTUSDT"},
        {"symbol": "IOTX", "source": "binance", "binance_symbol": "IOTXUSDT"},
        {"symbol": "FIL", "source": "binance", "binance_symbol": "FILUSDT"},
        {"symbol": "GRT", "source": "binance", "binance_symbol": "GRTUSDT"},
    ],
    "MEMECOIN": [
        # These are placeholders (liquid, Binance-listed memes) so the bot
        # runs out of the box. Swap in fresh pump.fun / low-cap DEX tokens
        # via dexscreener source as you find them - that's where this
        # strategy actually matters most.
        {"symbol": "DOGE", "source": "binance", "binance_symbol": "DOGEUSDT"},
        {"symbol": "PEPE", "source": "binance", "binance_symbol": "PEPEUSDT"},
        {"symbol": "WIF", "source": "binance", "binance_symbol": "WIFUSDT"},
        {"symbol": "BONK", "source": "binance", "binance_symbol": "BONKUSDT"},
        # Example of how you'd add a raw DEX shitcoin instead:
        # {"symbol": "SOMECOIN", "source": "dexscreener", "dex_chain": "solana",
        #  "dex_pair": "PASTE_PAIR_ADDRESS_FROM_DEXSCREENER_URL_HERE"},
    ],
}

# ---------------------------------------------------------------------------
# DETECTION THRESHOLDS
# ---------------------------------------------------------------------------
# How many candles define the "range" we check for contraction/breakout.
LOOKBACK_CANDLES = 40

# Bollinger Band width percentile threshold: current BBW must be below this
# percentile of its own recent history to count as "coiled" (accumulation).
BBW_CONTRACTION_PERCENTILE = 25

# Volume spike: current candle volume must be at least this multiple of the
# average volume over LOOKBACK_CANDLES to count as a breakout trigger.
VOLUME_SPIKE_MULTIPLIER = 2.0

# EMA period used as the "reclaim" level for breakout confirmation.
EMA_PERIOD = 21

# RSI period + the level it must cross up through (momentum confirmation).
RSI_PERIOD = 14
RSI_BREAKOUT_LEVEL = 55

# Minimum composite score (0-100) required to fire an alert.
ALERT_SCORE_THRESHOLD = 70

# DexScreener-only: minimum 1h liquidity change % to count as "liquidity
# building" (helps filter out pure wash-trading pumps with no real liquidity).
DEX_LIQUIDITY_GROWTH_THRESHOLD_PCT = 5.0

# Don't re-alert on the same token+timeframe more than once within this
# many minutes, even if it keeps scoring high.
ALERT_COOLDOWN_MINUTES = 60
