"""
state.py
--------
Tiny JSON-file state store. Used for two things:
  1. Alert cooldowns (don't spam the same signal every scan loop).
  2. DEX token history (DexScreener's free API has no OHLCV candles, so we
     track liquidity/volume ourselves scan-to-scan to detect *changes*).

Not a database - fine for a single-user personal bot polling every ~90s.
"""

import json
import os
import time

STATE_FILE = os.path.join(os.path.dirname(__file__), "bot_state.json")


def _load():
    if not os.path.exists(STATE_FILE):
        return {"cooldowns": {}, "dex_history": {}}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"cooldowns": {}, "dex_history": {}}


def _save(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def is_on_cooldown(key: str, cooldown_minutes: int) -> bool:
    state = _load()
    last = state["cooldowns"].get(key)
    if last is None:
        return False
    return (time.time() - last) < (cooldown_minutes * 60)


def set_cooldown(key: str):
    state = _load()
    state["cooldowns"][key] = time.time()
    _save(state)


def get_dex_history(key: str):
    """Returns last stored snapshot dict for a dex token key, or None."""
    state = _load()
    return state["dex_history"].get(key)


def set_dex_history(key: str, snapshot: dict):
    state = _load()
    state["dex_history"][key] = snapshot
    _save(state)
