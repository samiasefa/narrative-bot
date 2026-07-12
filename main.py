"""
main.py
-------
Entry point for running the bot as a continuous loop on your own always-on
machine (VPS, home server, etc). If you're using GitHub Actions instead,
you don't need this file - use run_scan_once.py.

Run with:  python main.py
Stop with: Ctrl+C
"""

import time
import traceback

import config
from scan_runner import run_once


def main():
    print("Narrative rotation / accumulation-breakout bot starting.")
    print(f"Tracking sectors: {list(config.SECTORS.keys())}")
    print(f"Scan interval: {config.SCAN_INTERVAL_SECONDS}s | "
          f"Alert threshold: {config.ALERT_SCORE_THRESHOLD}")

    while True:
        try:
            run_once()
        except Exception:
            print("[main] Unhandled error during scan:")
            traceback.print_exc()
        time.sleep(config.SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
