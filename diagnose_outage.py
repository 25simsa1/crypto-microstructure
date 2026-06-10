#!/usr/bin/env python3
"""Diagnose why a market-data logger stopped: exchange outage vs local outage vs network.

Encodes the 2026-06-10 Binance.US investigation as a repeatable script:

  1. Scan the venue's log files, classifying error lines as connection-level
     (TCP/TLS/handshake/keepalive — "couldn't reach the host") vs HTTP-level
     (503/500/403/451/429 — "host answered with an error").
  2. Check whether OTHER venues have data (parquet or jsonl.gz) written after
     the failure time — a live witness that the machine was up.
  3. Look for system sleep/wake/reboot evidence around the failure time
     (uptime, `last reboot`, pmset power log) — macOS compatible.
  4. Probe current connectivity to all venue endpoints plus Cloudflare DNS
     (a reachable-internet control).
  5. DNS resolution checks for every endpoint.
  6. Emit a verdict.

Stdlib only; system tools (curl, dig, last, uptime, pmset) via subprocess.

Usage:
  ./diagnose_outage.py --venue binance --time "06:34"
  ./diagnose_outage.py --venue kraken --time "03:10" --log-dir . --data-dir data
"""

import argparse
import datetime as dt
import glob
import os
import re
import subprocess
import sys

CONN_ERR_RE = re.compile(
    r"timed out|TimeoutError|handshake|ConnectionClosed|ConnectionReset"
    r"|ping timeout|refused|unreachable|reset by peer|EOF occurred",
    re.I,
)
HTTP_ERR_RE = re.compile(r"\b(503|500|502|504|403|451|429)\b|HTTP error|rejected", re.I)
LOG_TS_RE = re.compile(r"\[(\d{2}):(\d{2}):(\d{2})\]")

ENDPOINTS = {
    "binance": "https://api.binance.us/api/v3/ping",
    "binance-ws": "https://stream.binance.us:9443",
    "kraken": "https://ws.kraken.com",
    "coinbase-advanced": "https://advanced-trade-ws.coinbase.com",
    "coinbase-exchange-ws": "https://ws-feed.exchange.coinbase.com",
    "cloudflare-dns (control)": "https://1.1.1.1",
}
VENUES = ("binance", "kraken", "coinbase")


def sh(cmd, timeout=20):
    """Run a shell command, return (exit_code, stdout). Never raises."""
    try:
        p = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "(timed out)"
    except Exception as e:  # noqa: BLE001 — diagnostics must not crash
        return -1, f"(failed: {e})"


def section(title):
    print(f"\n=== {title} " + "=" * max(0, 60 - len(title)))


# ------------------------------------------------------------------ step 1

def scan_logs(venue, log_dir, fail_time):
    """Classify error lines in the venue's logs; find last activity time."""
    patterns = [os.path.join(log_dir, f"*{venue}*.log")]
    if venue == "binance":  # legacy loggers predate venue-named files
        patterns += [os.path.join(log_dir, n) for n in ("logger.log", "trades_logger.log")]
    files = sorted({f for p in patterns for f in glob.glob(p)})

    conn_errs, http_errs, last_ts = [], [], None
    for path in files:
        try:
            with open(path, errors="replace") as fh:
                lines = fh.readlines()
        except OSError:
            continue
        for line in lines:
            line = line.rstrip()
            m = LOG_TS_RE.search(line)
            if m:
                last_ts = m.group(0)
            if HTTP_ERR_RE.search(line):
                http_errs.append(f"{os.path.basename(path)}: {line}")
            elif "error" in line.lower() and CONN_ERR_RE.search(line):
                conn_errs.append(f"{os.path.basename(path)}: {line}")

    print(f"log files scanned: {[os.path.basename(f) for f in files] or 'NONE'}")
    print(f"connection-level errors: {len(conn_errs)}")
    for line in conn_errs[:3] + (["  ..."] if len(conn_errs) > 3 else []):
        print(f"  {line}")
    print(f"HTTP-level errors: {len(http_errs)}")
    for line in http_errs[:3]:
        print(f"  {line}")
    print(f"last log activity: {last_ts or 'unknown'}")
    logs_past_failure = bool(
        last_ts and fail_time and last_ts[1:6] > fail_time.strftime("%H:%M")
    )
    if logs_past_failure:
        print(f"-> logger kept writing AFTER {fail_time:%H:%M} (process survived the event)")
    return {
        "found_logs": bool(files),
        "conn_errs": len(conn_errs),
        "http_errs": len(http_errs),
        "logs_past_failure": logs_past_failure,
    }


# ------------------------------------------------------------------ step 2

def other_venue_data(venue, data_dir, fail_time):
    """Do other venues have parquet/jsonl.gz data written after the failure?"""
    alive_witness = False
    for other in VENUES:
        if other == venue:
            continue
        newest, newest_mtime = None, None
        for pat in (f"*{other}*.parquet", f"*{other}*.jsonl.gz"):
            for f in glob.glob(os.path.join(data_dir, pat)):
                mt = os.path.getmtime(f)
                if newest_mtime is None or mt > newest_mtime:
                    newest, newest_mtime = f, mt
        if newest is None:
            print(f"{other}: no data files")
            continue
        mtime = dt.datetime.fromtimestamp(newest_mtime)
        fresh = fail_time is None or mtime > fail_time
        print(f"{other}: newest {os.path.basename(newest)} "
              f"(modified {mtime:%Y-%m-%d %H:%M:%S}) "
              f"{'AFTER' if fresh else 'before'} failure time")
        if fresh:
            alive_witness = True
    return {"other_venue_after_failure": alive_witness}


# ------------------------------------------------------------------ step 3

def system_events(fail_time):
    """Sleep/wake/reboot evidence around the failure time (macOS)."""
    _, up = sh("uptime", timeout=5)
    print(f"uptime: {up.strip()}")
    _, rb = sh("last reboot | head -3", timeout=5)
    print(f"last reboot:\n{rb.strip()}")

    rebooted_today = dt.date.today().strftime("%b %e").replace("  ", " ") in rb
    slept = False
    if fail_time:
        lo = (fail_time - dt.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
        hi = (fail_time + dt.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
        _, pm = sh(
            "pmset -g log | grep -E 'Entering Sleep|Wake from|DarkWake from' | tail -200",
            timeout=30,
        )
        hits = [ln for ln in pm.splitlines() if lo <= ln[:16] <= hi]
        print(f"pmset sleep/wake events in [{lo} .. {hi}]: {len(hits)}")
        for ln in hits[:5]:
            print(f"  {ln.strip()}")
        slept = bool(hits)
    return {"rebooted_today": rebooted_today, "slept_near_failure": slept}


# ------------------------------------------------------------------ steps 4+5

def connectivity():
    """Probe each endpoint with curl; report HTTP code / timeout."""
    results = {}
    for name, url in ENDPOINTS.items():
        _, out = sh(
            f'curl -s -o /dev/null -w "%{{http_code}} %{{time_total}}s" --max-time 6 "{url}"',
            timeout=12,
        )
        code = out.strip().split()[0] if out.strip() else "000"
        # any HTTP response (even 4xx/5xx) proves the host is reachable
        reachable = code.isdigit() and code != "000"
        results[name] = reachable
        print(f"{name:28s} {url:45s} -> {out.strip()} "
              f"{'REACHABLE' if reachable else 'UNREACHABLE (no HTTP response)'}")
    return results


def dns_checks():
    ok = True
    for host in sorted({u.split("//")[1].split("/")[0].split(":")[0] for u in ENDPOINTS.values()}):
        if host.replace(".", "").isdigit():
            continue  # literal IP
        _, out = sh(f"dig +short +time=2 +tries=1 {host} | head -2", timeout=8)
        ips = out.strip().replace("\n", ", ")
        print(f"{host:38s} -> {ips or 'NO ANSWER'}")
        if not ips:
            ok = False
    return {"dns_ok": ok}


# ------------------------------------------------------------------ verdict

def verdict(ev):
    target_up = ev["target_reachable"]
    others_up = ev["others_reachable"]
    machine_alive = (
        ev["logs_past_failure"] or ev["other_venue_after_failure"]
    ) and not ev["rebooted_today"]

    if ev["slept_near_failure"] or ev["rebooted_today"]:
        return ("Local machine outage: sleep/reboot event near the failure time "
                "explains the stop.")
    if not ev["found_logs"]:
        return "Inconclusive: no log files found for this venue."
    if ev["http_errs"] > 0 and ev["conn_errs"] == 0:
        return ("Exchange-side API outage: the host answered with HTTP errors "
                "(503/500/403...), machine and network fine.")
    if ev["conn_errs"] > 0 and machine_alive:
        if not target_up and others_up and ev["dns_ok"]:
            return ("Selective upstream routing failure / network blackhole: "
                    "connection-level timeouts only (no HTTP errors), machine alive, "
                    "DNS fine, other endpoints reachable while the target is not. "
                    "(Indistinguishable from destination-side IP blocking without "
                    "an external vantage point.)")
        if not target_up:
            return ("Network issue (cannot reach host, no HTTP errors): "
                    "connection-level failures with the machine alive.")
        return ("Inconclusive: past connection errors but the target is reachable "
                "now — transient outage already resolved; logs are the only record.")
    return "Inconclusive: missing logs or conflicting evidence."


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--venue", default="binance", choices=VENUES)
    ap.add_argument("--time", default=None,
                    help='local failure time today, e.g. "06:34"')
    ap.add_argument("--log-dir", default=default_root)
    ap.add_argument("--data-dir", default=os.path.join(default_root, "data"))
    args = ap.parse_args()

    fail_time = None
    if args.time:
        h, m = args.time.split(":")
        fail_time = dt.datetime.now().replace(
            hour=int(h), minute=int(m), second=0, microsecond=0
        )

    print(f"Diagnosing: venue={args.venue}, failure time={args.time or 'unknown'}, "
          f"logs={args.log_dir}, data={args.data_dir}")

    ev = {}
    section("1. Log error classification")
    ev.update(scan_logs(args.venue, args.log_dir, fail_time))
    section("2. Other venues' data after failure")
    ev.update(other_venue_data(args.venue, args.data_dir, fail_time))
    section("3. System sleep/wake/reboot")
    ev.update(system_events(fail_time))
    section("4. Current endpoint connectivity")
    conn = connectivity()
    ev["target_reachable"] = conn.get(args.venue, conn.get("binance", False))
    ev["others_reachable"] = any(
        up for name, up in conn.items() if not name.startswith(args.venue)
    )
    section("5. DNS resolution")
    ev.update(dns_checks())

    section("VERDICT")
    print(verdict(ev))


if __name__ == "__main__":
    main()
