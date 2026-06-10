"""Data-quality validation over ingested snapshots and trades.

Checks performed per symbol:

* **Monotonic timestamps** — receive time should never go backwards.
* **Crossed books** — best bid >= best ask is impossible on a single venue
  and indicates a feed or parsing bug.
* **Gaps** — the book stream ticks ~1/s; a gap above ``gap_threshold_s``
  means a disconnect (the logger reconnects with backoff, so gaps are
  expected after errors, but they must be *known* before any analysis).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .ingest import BookSnapshot, Trade


@dataclass(frozen=True, slots=True)
class Gap:
    symbol: str
    start_ts: float
    end_ts: float

    @property
    def seconds(self) -> float:
        return self.end_ts - self.start_ts


@dataclass(slots=True)
class SymbolQuality:
    symbol: str
    n_snapshots: int = 0
    first_ts: float = 0.0
    last_ts: float = 0.0
    n_crossed: int = 0
    n_backwards_ts: int = 0
    gaps: list[Gap] = field(default_factory=list)

    @property
    def span_s(self) -> float:
        return self.last_ts - self.first_ts

    @property
    def gap_seconds(self) -> float:
        return sum(g.seconds for g in self.gaps)

    @property
    def coverage(self) -> float:
        """Fraction of the observed span not lost to gaps."""
        if self.span_s <= 0:
            return 1.0
        return 1.0 - self.gap_seconds / self.span_s


def validate_books(
    snapshots: Iterable[BookSnapshot], gap_threshold_s: float = 5.0
) -> dict[str, SymbolQuality]:
    """Single pass over snapshots, accumulating per-symbol quality stats."""
    out: dict[str, SymbolQuality] = {}
    for snap in snapshots:
        q = out.get(snap.symbol)
        if q is None:
            q = SymbolQuality(symbol=snap.symbol, first_ts=snap.ts, last_ts=snap.ts)
            out[snap.symbol] = q
        else:
            if snap.ts < q.last_ts:
                q.n_backwards_ts += 1
            elif snap.ts - q.last_ts > gap_threshold_s:
                q.gaps.append(Gap(snap.symbol, q.last_ts, snap.ts))
            q.last_ts = max(q.last_ts, snap.ts)
        if snap.is_crossed:
            q.n_crossed += 1
        q.n_snapshots += 1
    return out


def validate_trades(trades: Iterable[Trade]) -> dict[str, int]:
    """Count trades per symbol (sanity only; trades arrive irregularly)."""
    counts: dict[str, int] = {}
    for t in trades:
        counts[t.symbol] = counts.get(t.symbol, 0) + 1
    return counts


def _fmt_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def render_report(
    books: dict[str, SymbolQuality], trade_counts: dict[str, int]
) -> str:
    """Render a markdown data-quality report."""
    lines = ["# Data quality report", ""]
    for sym in sorted(books):
        q = books[sym]
        lines += [
            f"## {sym.upper()}",
            "",
            f"- snapshots: **{q.n_snapshots:,}** "
            f"({_fmt_ts(q.first_ts)} → {_fmt_ts(q.last_ts)})",
            f"- trades: **{trade_counts.get(sym, 0):,}**",
            f"- coverage: **{q.coverage:.2%}** "
            f"({q.gap_seconds:.0f}s lost across {len(q.gaps)} gap(s))",
            f"- crossed books: **{q.n_crossed}**"
            + (" ⚠️ investigate" if q.n_crossed else ""),
            f"- backwards timestamps: **{q.n_backwards_ts}**"
            + (" ⚠️ investigate" if q.n_backwards_ts else ""),
            "",
        ]
        if q.gaps:
            lines.append("| gap start | gap end | seconds |")
            lines.append("|---|---|---|")
            for g in q.gaps:
                lines.append(f"| {_fmt_ts(g.start_ts)} | {_fmt_ts(g.end_ts)} | {g.seconds:.1f} |")
            lines.append("")
    return "\n".join(lines)
