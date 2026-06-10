"""Convert raw jsonl.gz captures to Parquet, partitioned by symbol and hour.

Layout::

    parquet/
      books/symbol=btcusdt/hour=2026-06-10T05/data.parquet
      trades/symbol=btcusdt/hour=2026-06-10T05/data.parquet

Book rows are flattened to ``bid_px_0..N-1, bid_qty_0..N-1, ask_px_*,
ask_qty_*`` columns so downstream feature code is pure vectorized pandas.
Conversion is idempotent: an existing partition is rewritten only when the
source has more rows (the live hour grows between runs).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from .ingest import BookSnapshot, Trade, iter_book_snapshots, iter_trades

N_LEVELS = 20


def _hour_key(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%dT%H")


def _book_row(s: BookSnapshot) -> dict[str, float]:
    row: dict[str, float] = {"ts": s.ts}
    for i in range(N_LEVELS):
        bp, bq = s.bids[i] if i < len(s.bids) else (float("nan"), 0.0)
        ap, aq = s.asks[i] if i < len(s.asks) else (float("nan"), 0.0)
        row[f"bid_px_{i}"] = bp
        row[f"bid_qty_{i}"] = bq
        row[f"ask_px_{i}"] = ap
        row[f"ask_qty_{i}"] = aq
    return row


def _write_partitions(
    groups: dict[tuple[str, str], list[dict[str, float]]], root: Path
) -> list[Path]:
    written: list[Path] = []
    for (symbol, hour), rows in groups.items():
        part_dir = root / f"symbol={symbol}" / f"hour={hour}"
        out = part_dir / "data.parquet"
        if out.exists():
            existing = pd.read_parquet(out)
            if len(existing) >= len(rows):
                continue  # already up to date
        part_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).sort_values("ts").to_parquet(out, index=False)
        written.append(out)
    return written


def build_book_parquet(data_dir: Path, out_dir: Path) -> list[Path]:
    """Flatten all book captures into per-symbol/hour Parquet files."""
    groups: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)
    for snap in iter_book_snapshots(data_dir):
        groups[(snap.symbol, _hour_key(snap.ts))].append(_book_row(snap))
    return _write_partitions(groups, out_dir / "books")


def build_trade_parquet(data_dir: Path, out_dir: Path) -> list[Path]:
    """Convert all trade captures into per-symbol/hour Parquet files."""
    groups: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)
    for t in iter_trades(data_dir):
        groups[(t.symbol, _hour_key(t.ts))].append(
            {
                "ts": t.ts,
                "price": t.price,
                "qty": t.qty,
                "signed_qty": t.signed_qty,
            }
        )
    return _write_partitions(groups, out_dir / "trades")


def load_books(out_dir: Path, symbol: str) -> pd.DataFrame:
    """Load every book partition for a symbol, time-indexed and sorted."""
    parts = sorted((out_dir / "books" / f"symbol={symbol}").glob("hour=*/data.parquet"))
    if not parts:
        raise FileNotFoundError(f"no book parquet for {symbol} under {out_dir}")
    df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    df = df.sort_values("ts").reset_index(drop=True)
    df.index = pd.to_datetime(df["ts"], unit="s", utc=True)
    return df


def load_trades(out_dir: Path, symbol: str) -> pd.DataFrame:
    """Load every trade partition for a symbol, time-indexed and sorted."""
    parts = sorted((out_dir / "trades" / f"symbol={symbol}").glob("hour=*/data.parquet"))
    if not parts:
        raise FileNotFoundError(f"no trade parquet for {symbol} under {out_dir}")
    df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    df = df.sort_values("ts").reset_index(drop=True)
    df.index = pd.to_datetime(df["ts"], unit="s", utc=True)
    return df
