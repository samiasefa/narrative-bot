"""
run_scan_once.py
-----------------
Entry point for scheduled runners that execute a script once and exit
(GitHub Actions, cron, etc) rather than keeping a process alive forever.
GitHub Actions calls this file directly on a schedule.
"""

import sys
import traceback

print("run_scan_once.py starting...", flush=True)

try:
    from scan_runner import run_once
except Exception:
    print("Failed to import scan_runner:", flush=True)
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    try:
        run_once()
    except Exception:
        print("Scan crashed with an error:", flush=True)
        traceback.print_exc()
        sys.exit(1)
    print("run_scan_once.py finished.", flush=True)
