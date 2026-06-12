#!/usr/bin/env python3
"""Verify the venue trade capture is writing valid records.

Checks per venue/symbol: record validity (fields, types), counts, side
distribution, exchange-vs-receive clock skew, trade_ts monotonicity per
symbol, duplicate trade_ids, and price sanity against the concurrent
book capture (every trade within 50 bps of the prevailing book mid).
Exit code 0 only if every venue has valid trades for all three symbols.
"""

import itertools
import sys
from pathlib import Path

from microstructure.ingest import _iter_jsonl_gz
from microstructure.venue import (
    VENUE_SYMBOLS,
    VENUES,
    VenueBook,
    iter_venue_records,
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PRICE_SANITY_BPS = 50.0


def load_trades(venue: str) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for path in sorted(DATA.glob(f"trades-{venue}-2*.jsonl.gz")):
        for obj in _iter_jsonl_gz(Path(path)):
            if obj.get("type") == "trade":
                out.append(obj)
    return out


def book_mids(venue: str) -> dict[str, list[tuple[float, float]]]:
    """symbol -> [(ts, mid)] from the concurrent book capture, sorted."""
    mids: dict[str, list[tuple[float, float]]] = {s: [] for s in VENUE_SYMBOLS}
    for rec in iter_venue_records(DATA, venue):
        if isinstance(rec, VenueBook):
            mids[rec.symbol].append((rec.ts, (rec.best_bid + rec.best_ask) / 2))
    return mids


def prevailing_mid(mids: list[tuple[float, float]], ts: float) -> float | None:
    """Last book mid at or before ts (linear scan from the end; fine here)."""
    for t, m in reversed(mids):
        if t <= ts:
            return m
    return None


def main() -> int:
    ok = True
    for venue in VENUES:
        trades = load_trades(venue)
        print(f"\n=== {venue}: {len(trades)} trade records ===")
        if not trades:
            print("   FAIL: no trades captured")
            ok = False
            continue
        mids = book_mids(venue)
        for sym in VENUE_SYMBOLS:
            t_sym = [t for t in trades if t.get("symbol") == sym]
            if not t_sym:
                print(f"   {sym}: FAIL — no trades")
                ok = False
                continue
            bad_fields = [
                t for t in t_sym
                if not (
                    isinstance(t.get("price"), int | float)
                    and isinstance(t.get("qty"), int | float)
                    and t.get("side") in ("buy", "sell")
                    and isinstance(t.get("trade_ts"), int | float)
                    and t.get("trade_id")
                )
            ]
            buys = sum(1 for t in t_sym if t["side"] == "buy")
            ids = [str(t["trade_id"]) for t in t_sym]
            dupes = len(ids) - len(set(ids))
            tss = [float(t["trade_ts"]) for t in t_sym]  # type: ignore[arg-type]
            non_monotone = sum(1 for a, b in itertools.pairwise(tss) if b < a)
            skews = [
                float(t["ts"]) - float(t["trade_ts"])  # type: ignore[arg-type]
                for t in t_sym
            ]
            med_skew = sorted(skews)[len(skews) // 2]

            insane = 0
            checked = 0
            for t in t_sym:
                m = prevailing_mid(mids[sym], float(t["ts"]))  # type: ignore[arg-type]
                if m is None:
                    continue
                checked += 1
                if abs(float(t["price"]) - m) / m * 1e4 > PRICE_SANITY_BPS:  # type: ignore[arg-type]
                    insane += 1

            line_ok = not bad_fields and dupes == 0 and insane == 0
            status = "ok " if line_ok else "FAIL"
            if not line_ok:
                ok = False
            print(
                f"   {sym}: {status} {len(t_sym):4d} trades | buy share "
                f"{buys / len(t_sym):.0%} | bad fields {len(bad_fields)} | dup ids "
                f"{dupes} | ts inversions {non_monotone} | recv-exch skew "
                f"{med_skew * 1000:+.0f}ms | price vs book mid: {checked} checked, "
                f"{insane} outside {PRICE_SANITY_BPS:.0f}bps"
            )
    print(f"\noverall: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
