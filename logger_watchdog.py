#!/usr/bin/env python3
"""Read-only watchdog for the venue loggers.

Monitors process liveness, log freshness, data-file freshness, and recent
error patterns for each venue. Never touches the loggers themselves —
no kills, no restarts, no writes outside watchdog_status.json.
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
STATUS_FILE = BASE_DIR / "watchdog_status.json"

STALE_SECONDS = 120
ERROR_PATTERNS = ("ERROR", "Exception", "Timeout", "Connection")
CORE_VENUES = ("kraken", "coinbase")
OPTIONAL_VENUES = ("binance",)

GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"


def process_alive(venue):
    """True if a venue_logger.py process for this venue is running.

    Matches both `venue_logger.py --venue kraken` and the positional form
    `venue_logger.py kraken` that the loggers actually use.
    """
    result = subprocess.run(
        ["pgrep", "-f", f"venue_logger.py.*{venue}"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def latest_mtime(paths):
    """Most recent mtime among paths, or None if the list is empty."""
    mtimes = []
    for p in paths:
        try:
            mtimes.append(p.stat().st_mtime)
        except OSError:
            continue
    return max(mtimes) if mtimes else None


def find_log_file(venue):
    """Newest log file for a venue: logs/ dir first, then repo root."""
    candidates = []
    if LOGS_DIR.is_dir():
        candidates = list(LOGS_DIR.glob(f"*{venue}*.log"))
    if not candidates:
        candidates = list(BASE_DIR.glob(f"*{venue}*.log"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def find_data_files(venue):
    """Data files for a venue in data/: .parquet preferred, else any match."""
    if not DATA_DIR.is_dir():
        return []
    parquet = list(DATA_DIR.glob(f"{venue}*.parquet")) + list(
        DATA_DIR.glob(f"*{venue}*.parquet")
    )
    if parquet:
        return parquet
    return [p for p in DATA_DIR.glob(f"*{venue}*") if p.is_file()]


def count_recent_errors(log_path):
    """Count error-pattern hits in the last 20 lines of the log."""
    try:
        result = subprocess.run(
            ["tail", "-n", "20", str(log_path)],
            capture_output=True,
            text=True,
        )
        lines = result.stdout.splitlines()
    except OSError:
        return 0
    return sum(
        1 for line in lines if any(pat in line for pat in ERROR_PATTERNS)
    )


def age_seconds(mtime, now):
    return None if mtime is None else round(now - mtime, 1)


def check_venue(venue, now):
    alive = process_alive(venue)

    log_path = find_log_file(venue)
    log_age = age_seconds(
        latest_mtime([log_path]) if log_path else None, now
    )

    data_age = age_seconds(latest_mtime(find_data_files(venue)), now)

    error_count = count_recent_errors(log_path) if log_path else 0

    warnings = []
    if not alive:
        warnings.append("process dead")
    if log_age is None:
        warnings.append("no log file")
    elif log_age > STALE_SECONDS:
        warnings.append(f"log stale ({int(log_age)}s)")
    if data_age is None:
        warnings.append("no data files")
    elif data_age > STALE_SECONDS:
        warnings.append(f"data stale ({int(data_age)}s)")
    if error_count:
        warnings.append(f"{error_count} error line(s) in recent log")

    if not alive:
        status = "dead"
    elif warnings:
        status = "stale"
    else:
        status = "ok"

    return {
        "venue": venue,
        "status": status,
        "process_alive": alive,
        "log_file": str(log_path) if log_path else None,
        "log_age_seconds": log_age,
        "data_age_seconds": data_age,
        "recent_error_count": error_count,
        "warnings": warnings,
    }


def venue_has_data(venue):
    """Optional venues are only monitored if any trace of them exists."""
    return (
        find_log_file(venue) is not None
        or bool(find_data_files(venue))
        or process_alive(venue)
    )


def notify(message):
    """Fire a macOS notification; no-op on other platforms."""
    if sys.platform != "darwin":
        return
    safe = message.replace('"', "'")
    subprocess.run(
        [
            "osascript",
            "-e",
            f'display notification "{safe}" with title "Logger Watchdog"',
        ],
        capture_output=True,
    )


def print_status_line(result):
    color = {"ok": GREEN, "stale": YELLOW, "dead": RED}[result["status"]]
    log_age = result["log_age_seconds"]
    data_age = result["data_age_seconds"]
    parts = [
        f"proc={'up' if result['process_alive'] else 'DOWN'}",
        f"log={int(log_age)}s" if log_age is not None else "log=missing",
        f"data={int(data_age)}s" if data_age is not None else "data=missing",
        f"errors={result['recent_error_count']}",
    ]
    line = (
        f"{color}[{result['status'].upper():5}]{RESET} "
        f"{result['venue']:<9} {'  '.join(parts)}"
    )
    if result["warnings"]:
        line += f"  ({'; '.join(result['warnings'])})"
    print(line)


def run_check(notified):
    now = time.time()
    venues = list(CORE_VENUES) + [
        v for v in OPTIONAL_VENUES if venue_has_data(v)
    ]

    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"--- {timestamp} ---")

    results = [check_venue(v, now) for v in venues]
    for result in results:
        print_status_line(result)

    statuses = {r["status"] for r in results}
    if "dead" in statuses:
        overall = "dead"
    elif "stale" in statuses:
        overall = "stale"
    else:
        overall = "ok"

    status_doc = {
        "timestamp": timestamp,
        "overall": overall,
        "venues": {r["venue"]: r for r in results},
    }
    try:
        STATUS_FILE.write_text(json.dumps(status_doc, indent=2) + "\n")
    except OSError as exc:
        print(f"warning: could not write {STATUS_FILE}: {exc}")

    # Notify once per venue per distinct warning set; reset when healthy.
    for result in results:
        venue = result["venue"]
        key = tuple(result["warnings"])
        if result["warnings"]:
            if notified.get(venue) != key:
                notify(f"{venue}: {'; '.join(result['warnings'])}")
                notified[venue] = key
        else:
            notified.pop(venue, None)

    return overall


def main():
    parser = argparse.ArgumentParser(
        description="Read-only watchdog for venue loggers."
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=60.0,
        help="seconds between checks (default: 60)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="run a single check and exit",
    )
    args = parser.parse_args()

    notified = {}
    if args.once:
        overall = run_check(notified)
        sys.exit(0 if overall == "ok" else 1)

    try:
        while True:
            run_check(notified)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nwatchdog stopped")


if __name__ == "__main__":
    main()
