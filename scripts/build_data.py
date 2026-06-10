#!/usr/bin/env python3
"""Build/refresh the Parquet store and the data-quality report.

Usage: .venv/bin/python scripts/build_data.py
Safe to re-run any time; only stale partitions are rewritten.
"""

from pathlib import Path

from microstructure.ingest import iter_book_snapshots, iter_trades
from microstructure.parquet import build_book_parquet, build_trade_parquet
from microstructure.quality import render_report, validate_books, validate_trades

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PARQUET = ROOT / "parquet"


def main() -> None:
    books = build_book_parquet(DATA, PARQUET)
    trades = build_trade_parquet(DATA, PARQUET)
    print(f"parquet: {len(books)} book + {len(trades)} trade partitions (re)written")

    quality = validate_books(iter_book_snapshots(DATA))
    counts = validate_trades(iter_trades(DATA))
    report = render_report(quality, counts)
    out = ROOT / "output" / "data_quality.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(report)
    print(f"quality report -> {out}")
    for sym, q in sorted(quality.items()):
        print(
            f"  {sym}: {q.n_snapshots:,} snaps, coverage {q.coverage:.2%}, "
            f"{q.n_crossed} crossed, {q.n_backwards_ts} backwards-ts"
        )


if __name__ == "__main__":
    main()
