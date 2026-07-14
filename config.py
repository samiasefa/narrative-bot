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
TIMEFRAMES = ["5m", "15m"]
SCAN_INTERVAL_SECONDS = 90  # only used by main.py (continuous loop mode)

# ---------------------------------------------------------------------------
# SECTORS / TOKENS
# ---------------------------------------------------------------------------
# Each token entry:
#   symbol         -> display name
#   coingecko_id    -> used for market cap / FDV / "trending" lookups (always try to fill this in)
#   source          -> "binance" (full technical scan), "dexscreener" (DEX liquidity/volume scan),
#                       or "coingecko_only" (no technical scan - fundamentals + trending only)
#   binance_symbol  -> required if source == "binance"
#   dex_chain/dex_pair -> required if source == "dexscreener"
#
# IMPORTANT - read this: for tokens marked "coingecko_only" below, I either wasn't
# confident the token is listed on Binance, or the ticker was too generic/collision-prone
# to guess safely (wrong guesses can silently pull the WRONG coin's data). Tokens marked
# "binance" but commented "verify" are my best guess, not a guarantee - Binance listings
# change often. If a token never produces technical scores, it's not on Binance under
# that symbol; either leave it as fundamentals-only, or find its real pair on Binance /
# DexScreener yourself and update the entry.
#
# To fix a coingecko_id: go to coingecko.com, search the token, the id is in the URL
# (coingecko.com/en/coins/THIS-PART-HERE).

SECTORS = {
    "RWA": [
        {"symbol": "ONDO", "coingecko_id": "ondo-finance", "source": "binance", "binance_symbol": "ONDOUSDT"},
        {"symbol": "LINK", "coingecko_id": "chainlink", "source": "binance", "binance_symbol": "LINKUSDT"},
        {"symbol": "MKR", "coingecko_id": "maker", "source": "binance", "binance_symbol": "MKRUSDT"},
        {"symbol": "SKY", "coingecko_id": "sky", "source": "binance", "binance_symbol": "SKYUSDT"},
        {"symbol": "CFG", "coingecko_id": "centrifuge", "source": "binance", "binance_symbol": "CFGUSDT"},
        {"symbol": "MPL", "coingecko_id": "maple-finance", "source": "coingecko_only"},
        {"symbol": "GFI", "coingecko_id": "goldfinch-finance", "source": "coingecko_only"},
        {"symbol": "PENDLE", "coingecko_id": "pendle", "source": "binance", "binance_symbol": "PENDLEUSDT"},
        {"symbol": "CC", "coingecko_id": "canton-network", "source": "coingecko_only"},
        {"symbol": "TRU", "coingecko_id": "truefi", "source": "binance", "binance_symbol": "TRUUSDT"},
        {"symbol": "NXRA", "coingecko_id": "nexera", "source": "coingecko_only"},
    ],
    "AI": [
        {"symbol": "TAO", "coingecko_id": "bittensor", "source": "binance", "binance_symbol": "TAOUSDT"},
        {"symbol": "FET", "coingecko_id": "fetch-ai", "source": "binance", "binance_symbol": "FETUSDT"},
        {"symbol": "RENDER", "coingecko_id": "render-token", "source": "binance", "binance_symbol": "RENDERUSDT"},
        {"symbol": "NEAR", "coingecko_id": "near", "source": "binance", "binance_symbol": "NEARUSDT"},
        {"symbol": "AKT", "coingecko_id": "akash-network", "source": "binance", "binance_symbol": "AKTUSDT"},
        {"symbol": "ATH", "coingecko_id": "aethir", "source": "binance", "binance_symbol": "ATHUSDT"},
        {"symbol": "ARKM", "coingecko_id": "arkham", "source": "binance", "binance_symbol": "ARKMUSDT"},
        {"symbol": "WLD", "coingecko_id": "worldcoin-wld", "source": "binance", "binance_symbol": "WLDUSDT"},
        {"symbol": "LPT", "coingecko_id": "livepeer", "source": "coingecko_only"},
        {"symbol": "GRT", "coingecko_id": "the-graph", "source": "binance", "binance_symbol": "GRTUSDT"},
    ],
    "DEPIN": [
        {"symbol": "HNT", "coingecko_id": "helium", "source": "binance", "binance_symbol": "HNTUSDT"},
        {"symbol": "HONEY", "coingecko_id": "hivemapper", "source": "coingecko_only"},
        {"symbol": "FIL", "coingecko_id": "filecoin", "source": "binance", "binance_symbol": "FILUSDT"},
        {"symbol": "AR", "coingecko_id": "arweave", "source": "binance", "binance_symbol": "ARUSDT"},
        {"symbol": "GRASS", "coingecko_id": "grass", "source": "binance", "binance_symbol": "GRASSUSDT"},
        {"symbol": "JASMY", "coingecko_id": "jasmycoin", "source": "binance", "binance_symbol": "JASMYUSDT"},
        {"symbol": "THETA", "coingecko_id": "theta-token", "source": "binance", "binance_symbol": "THETAUSDT"},
        {"symbol": "GEOD", "coingecko_id": "geodnet", "source": "coingecko_only"},
        {"symbol": "IO", "coingecko_id": "io", "source": "coingecko_only"},
        {"symbol": "NOS", "coingecko_id": "nosana", "source": "coingecko_only"},
    ],
    "L1": [
        {"symbol": "SOL", "coingecko_id": "solana", "source": "binance", "binance_symbol": "SOLUSDT"},
        {"symbol": "SUI", "coingecko_id": "sui", "source": "binance", "binance_symbol": "SUIUSDT"},
        {"symbol": "SEI", "coingecko_id": "sei-network", "source": "binance", "binance_symbol": "SEIUSDT"},
        {"symbol": "APT", "coingecko_id": "aptos", "source": "binance", "binance_symbol": "APTUSDT"},
        {"symbol": "AVAX", "coingecko_id": "avalanche-2", "source": "binance", "binance_symbol": "AVAXUSDT"},
        {"symbol": "FTM/S", "coingecko_id": "fantom", "source": "binance", "binance_symbol": "FTMUSDT"},
        {"symbol": "INJ", "coingecko_id": "injective-protocol", "source": "binance", "binance_symbol": "INJUSDT"},
        {"symbol": "HYPE", "coingecko_id": "hyperliquid", "source": "coingecko_only"},
        {"symbol": "TON", "coingecko_id": "the-open-network", "source": "binance", "binance_symbol": "TONUSDT"},
    ],
    "MEMECOIN": [
        {"symbol": "DOGE", "coingecko_id": "dogecoin", "source": "binance", "binance_symbol": "DOGEUSDT"},
        {"symbol": "SHIB", "coingecko_id": "shiba-inu", "source": "binance", "binance_symbol": "SHIBUSDT"},
        {"symbol": "PEPE", "coingecko_id": "pepe", "source": "binance", "binance_symbol": "PEPEUSDT"},
        {"symbol": "WIF", "coingecko_id": "dogwifcoin", "source": "binance", "binance_symbol": "WIFUSDT"},
        {"symbol": "BONK", "coingecko_id": "bonk", "source": "binance", "binance_symbol": "BONKUSDT"},
        {"symbol": "FLOKI", "coingecko_id": "floki", "source": "binance", "binance_symbol": "FLOKIUSDT"},
        {"symbol": "POPCAT", "coingecko_id": "popcat", "source": "coingecko_only"},
        {"symbol": "BRETT", "coingecko_id": "based-brett", "source": "coingecko_only"},
        {"symbol": "MOG", "coingecko_id": "mog-coin", "source": "coingecko_only"},
        {"symbol": "BOME", "coingecko_id": "book-of-meme", "source": "binance", "binance_symbol": "BOMEUSDT"},
    ],
}

# ---------------------------------------------------------------------------
# DETECTION THRESHOLDS (technical - Binance/DexScreener tokens)
# ---------------------------------------------------------------------------
LOOKBACK_CANDLES = 40
BBW_CONTRACTION_PERCENTILE = 25
VOLUME_SPIKE_MULTIPLIER = 2.0
EMA_PERIOD = 21
RSI_PERIOD = 14
RSI_BREAKOUT_LEVEL = 55
ALERT_SCORE_THRESHOLD = 70
DEX_LIQUIDITY_GROWTH_THRESHOLD_PCT = 5.0
ALERT_COOLDOWN_MINUTES = 60

# ---------------------------------------------------------------------------
# COINGECKO (fundamentals + trending/social-attention signal)
# ---------------------------------------------------------------------------
COINGECKO_ENABLED = True
TRENDING_BONUS_POINTS = 20
FDV_MCAP_WARNING_RATIO = 3.0
