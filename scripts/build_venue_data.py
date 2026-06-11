#!/usr/bin/env python3
"""Build/refresh the dual-venue Parquet store and the venue quality report.

Safe to re-run; only grown partitions are rewritten. Reads data/ only —
never touches the live loggers.
"""

from pathlib import Path

from microstructure.venue import VENUES, build_venue_parquet, render_venue_report, venue_quality

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PARQUET = ROOT / "parquet"


def main() -> None:
    written = build_venue_parquet(DATA, PARQUET)
    print(f"venue parquet: {len(written)} partitions (re)written")
    quality = {v: venue_quality(DATA, v) for v in VENUES}
    out = ROOT / "output" / "venue_quality.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(render_venue_report(quality))
    print(f"venue quality report -> {out}")
    for venue, syms in quality.items():
        for sym, q in sorted(syms.items()):
            med, p95 = q.cadence()
            print(
                f"  {venue}/{sym}: {q.n_snapshots:,} snaps, {q.span_s / 3600:.1f}h, "
                f"coverage {q.coverage:.2%}, cadence {med:.2f}/{p95:.2f}s, "
                f"{q.n_crossed} crossed, {q.n_locked} locked"
            )


if __name__ == "__main__":
    main()
