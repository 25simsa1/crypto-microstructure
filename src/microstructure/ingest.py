"""Typed ingestion of the raw jsonl.gz files written by the live loggers.

The loggers append one JSON object per line to hourly-rotated gzip files:

* ``book-YYYYMMDD-HH.jsonl.gz`` — top-20 order book snapshots, ~1/s/symbol
* ``trades-YYYYMMDD-HH.jsonl.gz`` — individual trades with aggressor side

Files may still be open for writing; readers must tolerate a truncated gzip
tail (``EOFError``) and a torn final JSON line.
"""

from __future__ import annotations

import glob
import gzip
import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class BookSnapshot:
    """One top-of-book snapshot. Levels are (price, qty), best price first."""

    ts: float  # unix seconds, local receive time
    symbol: str
    bids: tuple[tuple[float, float], ...]
    asks: tuple[tuple[float, float], ...]

    @property
    def best_bid(self) -> float:
        return self.bids[0][0]

    @property
    def best_ask(self) -> float:
        return self.asks[0][0]

    @property
    def mid(self) -> float:
        return (self.best_bid + self.best_ask) / 2.0

    @property
    def is_crossed(self) -> bool:
        """True if best bid >= best ask (should never happen on one venue)."""
        return self.best_bid >= self.best_ask


@dataclass(frozen=True, slots=True)
class Trade:
    """One trade print. ``buyer_maker`` True means the aggressor was a seller."""

    ts: float  # unix seconds, exchange event time
    symbol: str
    price: float
    qty: float
    buyer_maker: bool

    @property
    def signed_qty(self) -> float:
        """Quantity signed by aggressor direction (+ = buy aggressor)."""
        return -self.qty if self.buyer_maker else self.qty


def _iter_jsonl_gz(path: Path) -> Iterator[dict[str, object]]:
    """Yield parsed JSON objects, tolerating a live (truncated) gzip tail."""
    with gzip.open(path, "rt") as fh:
        while True:
            try:
                line = fh.readline()
            except EOFError:
                return  # unflushed tail of a file still being written
            if not line:
                return
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue  # torn line from a crash mid-write
            if isinstance(obj, dict):
                yield obj


def _level(raw: object) -> tuple[float, float]:
    price, qty = raw  # type: ignore[misc]
    return float(price), float(qty)


def iter_book_snapshots(data_dir: Path) -> Iterator[BookSnapshot]:
    """Yield every book snapshot under ``data_dir`` in file order.

    Within one file, snapshots for different symbols are interleaved in
    arrival order. Empty-side snapshots are skipped (cannot price them).
    """
    for name in sorted(glob.glob(str(data_dir / "book-*.jsonl.gz"))):
        for obj in _iter_jsonl_gz(Path(name)):
            bids = tuple(_level(x) for x in obj["bids"])  # type: ignore[union-attr, arg-type]
            asks = tuple(_level(x) for x in obj["asks"])  # type: ignore[union-attr, arg-type]
            if not bids or not asks:
                continue
            yield BookSnapshot(
                ts=float(obj["ts"]),  # type: ignore[arg-type]
                symbol=str(obj["symbol"]),
                bids=bids,
                asks=asks,
            )


def iter_trades(data_dir: Path) -> Iterator[Trade]:
    """Yield every trade under ``data_dir`` in file order."""
    for name in sorted(glob.glob(str(data_dir / "trades-*.jsonl.gz"))):
        for obj in _iter_jsonl_gz(Path(name)):
            yield Trade(
                ts=float(obj["ts"]),  # type: ignore[arg-type]
                symbol=str(obj["symbol"]),
                price=float(obj["price"]),  # type: ignore[arg-type]
                qty=float(obj["qty"]),  # type: ignore[arg-type]
                buyer_maker=bool(obj["buyer_maker"]),
            )
