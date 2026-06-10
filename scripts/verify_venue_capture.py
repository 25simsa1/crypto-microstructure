#!/usr/bin/env python3
"""Quality check for the multi-venue capture (venue_logger.py output).

Reads every data/book-{kraken,coinbase}-*.jsonl.gz and reports, per
venue/symbol: snapshot count, time span, median inter-snapshot gap, max gap,
crossed books, level counts, plus heartbeat lines seen per venue.
Exits non-zero if any venue/symbol has zero snapshots or any crossed book.
"""

import glob
import gzip
import json
import statistics
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

ok = True
for venue in ("kraken", "coinbase"):
    per_sym: dict[str, list] = {}
    heartbeats = 0
    crossed = 0
    bad_levels = 0
    for path in sorted(glob.glob(str(DATA_DIR / f"book-{venue}-*.jsonl.gz"))):
        with gzip.open(path, "rt") as fh:
            lines = []
            try:
                for line in fh:
                    lines.append(line)
            except EOFError:
                # file is still being appended; the unflushed tail is in flight
                pass
            for line in lines:
                if not line.endswith("\n"):
                    continue  # partial trailing line
                rec = json.loads(line)
                if rec["type"] == "heartbeat":
                    heartbeats += 1
                    continue
                per_sym.setdefault(rec["symbol"], []).append(rec["ts"])
                bb, ba = rec["bids"][0][0], rec["asks"][0][0]
                if bb >= ba:
                    crossed += 1
                if len(rec["bids"]) < 5 or len(rec["asks"]) < 5:
                    bad_levels += 1
    print(f"\n== {venue}: {heartbeats} heartbeat lines, "
          f"{crossed} crossed books, {bad_levels} thin (<5 level) snapshots")
    if crossed:
        ok = False
    if not per_sym:
        print("   NO SNAPSHOTS AT ALL")
        ok = False
    for sym, tss in sorted(per_sym.items()):
        tss.sort()
        gaps = [b - a for a, b in zip(tss, tss[1:])]
        span = tss[-1] - tss[0]
        print(f"   {sym}: {len(tss)} snapshots over {span:.0f}s | "
              f"median gap {statistics.median(gaps):.2f}s | max gap {max(gaps):.2f}s")
        if not tss:
            ok = False

sys.exit(0 if ok else 1)
