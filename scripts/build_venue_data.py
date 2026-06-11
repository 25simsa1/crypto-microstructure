#!/usr/bin/env python3
"""Build/refresh the dual-venue Parquet store and the venue quality report.

Safe to re-run; only grown partitions are rewritten. Reads data/ only —
never touches the live loggers.
"""

from pathlib import Path

from microstructure.venue import (
    VENUE_SYMBOLS,
    VENUES,
    build_venue_parquet,
    load_venue_books,
    render_venue_report,
    stale_episodes,
    venue_quality,
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PARQUET = ROOT / "parquet"


def main() -> None:
    written = build_venue_parquet(DATA, PARQUET)
    print(f"venue parquet: {len(written)} partitions (re)written")
    quality = {v: venue_quality(DATA, v) for v in VENUES}
    report = render_venue_report(quality)

    # staleness: snapshots arriving on schedule but book content frozen
    stale_lines = ["", "## Stale books (content frozen >=120s while snapshots arrive)", ""]
    any_stale = False
    for venue in VENUES:
        for sym in VENUE_SYMBOLS:
            try:
                book = load_venue_books(PARQUET, venue, sym)
            except FileNotFoundError:
                continue
            for start, end in stale_episodes(book, min_s=120.0):
                any_stale = True
                dur = (end - start).total_seconds()
                stale_lines.append(
                    f"- **{venue}/{sym}**: {start:%m-%d %H:%M:%S} → "
                    f"{end:%H:%M:%S} UTC ({dur / 60:.0f} min)"
                )
    if not any_stale:
        stale_lines.append("None detected.")
    report += "\n".join(stale_lines)

    out = ROOT / "output" / "venue_quality.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(report)
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
