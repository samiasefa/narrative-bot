"""
telegram_notifier.py
---------------------
Sends alert messages to your Telegram via the Bot API.

Setup:
  1. Message @BotFather on Telegram, /newbot, follow prompts -> get a bot token.
  2. Message your new bot anything (so it can see your chat).
  3. Visit https://api.telegram.org/bot<TOKEN>/getUpdates in a browser and
     find your "chat":{"id": ...} value.
  4. Put both into config.py (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) or set
     them as environment variables of the same name.
"""

import requests

import config


def send_alert(result: dict):
    text = format_alert(result)
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[telegram_notifier] Failed to send alert: {e}")


def _format_dollars(n):
    if n is None:
        return "n/a"
    if n >= 1_000_000_000:
        return f"${n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"${n / 1_000:.0f}K"
    return f"${n:.0f}"


def format_alert(result: dict) -> str:
    symbol = result["symbol"]
    sector = result["sector"]
    score = result["score"]
    tf = result.get("timeframe", "n/a")
    price = result.get("last_price")
    reasons = result.get("reasons", [])

    lines = [
        f"*{symbol}* ({sector}) — score {score}",
        f"Timeframe: {tf} | Source: {result['source']}",
        f"Price: {price}",
    ]

    mc, fdv = result.get("market_cap"), result.get("fdv")
    if mc or fdv:
        lines.append(f"Market cap: {_format_dollars(mc)} | FDV: {_format_dollars(fdv)}")

    if result.get("low_float_warning"):
        lines.append(f"⚠️ {result['low_float_warning']}")

    lines.append("")
    lines.append("Signals:")
    lines += [f"• {r}" for r in reasons]
    return "\n".join(lines)
