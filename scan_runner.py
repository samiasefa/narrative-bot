"""
scan_runner.py
---------------
The actual "do one scan pass" logic, shared by:
  - main.py (loops this forever - use if running on your own always-on machine)
  - run_scan_once.py (single pass then exit - use for GitHub Actions / cron)
"""

from datetime import datetime

import config
from accumulation_scanner import scan_all_sectors
from state import is_on_cooldown, set_cooldown
from telegram_notifier import send_alert


def run_once():
    print(f"\n[{datetime.now().isoformat(timespec='seconds')}] Scanning...")
    results = scan_all_sectors()

    fired = 0
    for res in sorted(results, key=lambda r: r["score"], reverse=True):
        flag = "🔥" if res["score"] >= config.ALERT_SCORE_THRESHOLD else "  "
        print(f"{flag} {res['sector']:10s} {res['symbol']:8s} "
              f"[{res.get('timeframe', 'n/a'):4s}] score={res['score']:3d} "
              f"reasons={'; '.join(res['reasons']) if res['reasons'] else '-'}")

        if res["score"] < config.ALERT_SCORE_THRESHOLD:
            continue

        cooldown_key = f"{res['source']}:{res['symbol']}:{res.get('timeframe', 'n/a')}"
        if is_on_cooldown(cooldown_key, config.ALERT_COOLDOWN_MINUTES):
            continue

        send_alert(res)
        set_cooldown(cooldown_key)
        fired += 1

    print(f"Scan complete. {len(results)} checks run, {fired} alert(s) sent.")
    return fired
