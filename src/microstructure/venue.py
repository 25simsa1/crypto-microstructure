"""Dual-venue (Kraken / Coinbase) capture: ingestion, Parquet, quality.

``venue_logger.py`` writes ``data/book-{venue}-YYYYMMDD-HH.jsonl.gz``
with two record types::

    {"ts", "venue", "symbol", "type": "book", "bids": [[p, q], ...],
     "asks": [[p, q], ...]}
    {"ts", "venue", "type": "heartbeat", "snapshots": <cumulative>,
     "connected": bool, "reconnects": int, "uptime_s": float}

Heartbeats arrive every ~60 s whether or not the feed is healthy, which
lets the quality report *attribute* gaps: a gap with heartbeats whose
``connected`` is false (or whose snapshot counter is flat) is a feed
outage; a gap with no heartbeats at all means the logger process itself
was not running (e.g. machine asleep).
"""

from __future__ import annotations

import glob
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pandas as pd

from .ingest import _iter_jsonl_gz
from .parquet import _book_row, _hour_key, _write_partitions

VENUES = ("kraken", "coinbase")
VENUE_SYMBOLS = ("BTC-USD", "ETH-USD", "SOL-USD")


@dataclass(frozen=True, slots=True)
class VenueBook:
    """One venue book snapshot. Levels are (price, qty), best first."""

    ts: float
    venue: str
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
    def is_crossed(self) -> bool:
        return self.best_bid > self.best_ask

    @property
    def is_locked(self) -> bool:
        return self.best_bid == self.best_ask


@dataclass(frozen=True, slots=True)
class Heartbeat:
    ts: float
    venue: str
    snapshots: int  # cumulative count written by the logger
    connected: bool
    reconnects: int


def _num_level(raw: object) -> tuple[float, float]:
    price, qty = cast("tuple[float, float]", raw)  # numeric in venue files
    return float(price), float(qty)


def iter_venue_records(
    data_dir: Path, venue: str
) -> Iterator[VenueBook | Heartbeat]:
    """Yield books and heartbeats for one venue in file order."""
    for name in sorted(glob.glob(str(data_dir / f"book-{venue}-*.jsonl.gz"))):
        for obj in _iter_jsonl_gz(Path(name)):
            if obj.get("type") == "heartbeat":
                yield Heartbeat(
                    ts=cast("float", obj["ts"]),
                    venue=str(obj["venue"]),
                    snapshots=cast("int", obj["snapshots"]),
                    connected=bool(obj["connected"]),
                    reconnects=cast("int", obj["reconnects"]),
                )
            elif obj.get("type") == "book":
                bids = tuple(_num_level(x) for x in cast("list[object]", obj["bids"]))
                asks = tuple(_num_level(x) for x in cast("list[object]", obj["asks"]))
                if not bids or not asks:
                    continue
                yield VenueBook(
                    ts=cast("float", obj["ts"]),
                    venue=str(obj["venue"]),
                    symbol=str(obj["symbol"]),
                    bids=bids,
                    asks=asks,
                )


def build_venue_parquet(data_dir: Path, out_dir: Path) -> list[Path]:
    """Flatten venue books into parquet/venue_books/venue=V/symbol=S/hour=H."""
    written: list[Path] = []
    for venue in VENUES:
        groups: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)
        for rec in iter_venue_records(data_dir, venue):
            if isinstance(rec, VenueBook):
                groups[(rec.symbol, _hour_key(rec.ts))].append(
                    _book_row_from_venue(rec)
                )
        root = out_dir / "venue_books" / f"venue={venue}"
        written += _write_partitions(groups, root)
    return written


def _book_row_from_venue(rec: VenueBook) -> dict[str, float]:
    # reuse the night-one flattener via a duck-typed shim
    return _book_row(rec)  # type: ignore[arg-type]


def load_venue_books(out_dir: Path, venue: str, symbol: str) -> pd.DataFrame:
    """Load every partition for a venue/symbol, time-indexed and sorted."""
    parts = sorted(
        (out_dir / "venue_books" / f"venue={venue}" / f"symbol={symbol}").glob(
            "hour=*/data.parquet"
        )
    )
    if not parts:
        raise FileNotFoundError(f"no parquet for {venue}/{symbol} under {out_dir}")
    df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    df = df.sort_values("ts").reset_index(drop=True)
    df.index = pd.to_datetime(df["ts"], unit="s", utc=True)
    return df


# ---------------------------------------------------------------------------
# quality with heartbeat-attributed gaps
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class VenueGap:
    venue: str
    symbol: str
    start_ts: float
    end_ts: float
    attribution: str  # 'feed-outage' | 'logger-down' | 'symbol-quiet' | 'unattributed-short'

    @property
    def seconds(self) -> float:
        return self.end_ts - self.start_ts


@dataclass(slots=True)
class VenueSymbolQuality:
    venue: str
    symbol: str
    n_snapshots: int = 0
    first_ts: float = 0.0
    last_ts: float = 0.0
    n_crossed: int = 0
    n_locked: int = 0
    n_backwards_ts: int = 0
    dts: list[float] = field(default_factory=list)  # inter-snapshot deltas
    gaps: list[VenueGap] = field(default_factory=list)

    @property
    def span_s(self) -> float:
        return self.last_ts - self.first_ts

    @property
    def coverage(self) -> float:
        if self.span_s <= 0:
            return 1.0
        return 1.0 - sum(g.seconds for g in self.gaps) / self.span_s

    def cadence(self) -> tuple[float, float]:
        """(median, p95) inter-snapshot interval in seconds."""
        if not self.dts:
            return (float("nan"), float("nan"))
        s = pd.Series(self.dts)
        return (float(s.median()), float(s.quantile(0.95)))


def _attribute(gap_start: float, gap_end: float, beats: list[Heartbeat]) -> str:
    """Classify a gap using the heartbeats that fall inside it."""
    inside = [b for b in beats if gap_start < b.ts < gap_end]
    if not inside:
        # heartbeats come every ~60 s: a short gap can miss one by chance,
        # so absence of heartbeats is only evidence on longer gaps
        if gap_end - gap_start >= 90.0:
            return "logger-down"
        return "unattributed-short"
    if any(not b.connected for b in inside):
        return "feed-outage"
    # counter flat across >=2 heartbeats -> nothing written venue-wide
    if len(inside) >= 2 and inside[-1].snapshots == inside[0].snapshots:
        return "feed-outage"
    return "symbol-quiet"  # logger alive and writing other symbols


def venue_quality(
    data_dir: Path, venue: str, gap_threshold_s: float = 5.0
) -> dict[str, VenueSymbolQuality]:
    """Single pass: per-symbol quality with heartbeat-attributed gaps."""
    beats: list[Heartbeat] = []
    out: dict[str, VenueSymbolQuality] = {}
    raw_gaps: list[tuple[str, float, float]] = []
    for rec in iter_venue_records(data_dir, venue):
        if isinstance(rec, Heartbeat):
            beats.append(rec)
            continue
        q = out.get(rec.symbol)
        if q is None:
            q = VenueSymbolQuality(
                venue=venue, symbol=rec.symbol, first_ts=rec.ts, last_ts=rec.ts
            )
            out[rec.symbol] = q
        else:
            dt = rec.ts - q.last_ts
            if dt < 0:
                q.n_backwards_ts += 1
            else:
                q.dts.append(dt)
                if dt > gap_threshold_s:
                    raw_gaps.append((rec.symbol, q.last_ts, rec.ts))
            q.last_ts = max(q.last_ts, rec.ts)
        if rec.is_crossed:
            q.n_crossed += 1
        if rec.is_locked:
            q.n_locked += 1
        q.n_snapshots += 1
    for symbol, start, end in raw_gaps:
        out[symbol].gaps.append(
            VenueGap(venue, symbol, start, end, _attribute(start, end, beats))
        )
    return out


def _fmt_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%m-%d %H:%M:%S")


def render_venue_report(quality: dict[str, dict[str, VenueSymbolQuality]]) -> str:
    """Markdown report comparing venues side by side."""
    lines = [
        "# Venue capture quality (Kraken vs Coinbase)",
        "",
        "| venue | symbol | snapshots | span (h) | coverage | cadence med/p95 (s) "
        "| crossed | locked | backwards ts |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    all_gaps: list[VenueGap] = []
    for venue in sorted(quality):
        for symbol in sorted(quality[venue]):
            q = quality[venue][symbol]
            med, p95 = q.cadence()
            lines.append(
                f"| {venue} | {symbol} | {q.n_snapshots:,} | {q.span_s / 3600:.1f} "
                f"| {q.coverage:.2%} | {med:.2f} / {p95:.2f} | {q.n_crossed} "
                f"| {q.n_locked} | {q.n_backwards_ts} |"
            )
            all_gaps += q.gaps
    lines += ["", "## Gaps (heartbeat-attributed)", ""]
    if not all_gaps:
        lines.append("None above threshold.")
    else:
        by_kind: dict[str, list[VenueGap]] = defaultdict(list)
        for g in all_gaps:
            by_kind[g.attribution].append(g)
        lines += [
            "| attribution | count | total s | longest |",
            "|---|---|---|---|",
        ]
        for kind in sorted(by_kind):
            gs = by_kind[kind]
            longest = max(gs, key=lambda g: g.seconds)
            lines.append(
                f"| {kind} | {len(gs)} | {sum(g.seconds for g in gs):,.0f} "
                f"| {longest.seconds:,.0f}s ({longest.venue}/{longest.symbol} "
                f"@ {_fmt_ts(longest.start_ts)}) |"
            )
        lines += [
            "",
            "`feed-outage` = logger heartbeating but disconnected/not writing; "
            "`logger-down` = no heartbeats inside a >=90s gap (process not "
            "running, e.g. machine asleep); `symbol-quiet` = logger alive and "
            "writing, this symbol silent; `unattributed-short` = gap too short "
            "for heartbeat evidence either way.",
        ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# staleness: snapshots keep arriving but the book content is frozen
# ---------------------------------------------------------------------------


def stale_mask(book: pd.DataFrame, min_s: float = 120.0) -> pd.Series:
    """True where the top of book has been unchanged for >= ``min_s``.

    Catches the failure mode where a logger keeps writing snapshots on
    schedule (cadence and heartbeats look healthy) but the per-symbol
    book state stopped updating — observed live on Coinbase/ETH-USD,
    frozen for 90+ minutes while Kraken moved ~2%.
    """
    top = book[["bid_px_0", "ask_px_0", "bid_qty_0", "ask_qty_0"]]
    changed = top.ne(top.shift()).any(axis=1)
    changed.iloc[0] = True
    group = changed.cumsum()
    run_start = book["ts"].groupby(group).transform("first")
    # require snapshots to actually be ARRIVING while frozen — otherwise a
    # data gap (machine asleep) with an unchanged book across it would be
    # misread as staleness; at ~1 snap/s demand at least min_s/2 of them
    snaps_in_run = group.groupby(group).cumcount()
    return ((book["ts"] - run_start) >= min_s) & (snaps_in_run >= min_s / 2)


def stale_episodes(
    book: pd.DataFrame, min_s: float = 120.0
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Contiguous (start, end) spans where ``stale_mask`` is True."""
    m = stale_mask(book, min_s)
    out: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    start: pd.Timestamp | None = None
    prev: pd.Timestamp | None = None
    for ts, flag in m.items():
        if flag and start is None:
            start = ts
        elif not flag and start is not None:
            assert prev is not None
            out.append((start, prev))
            start = None
        prev = ts
    if start is not None and prev is not None:
        out.append((start, prev))
    return out
