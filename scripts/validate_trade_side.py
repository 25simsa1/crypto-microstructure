#!/usr/bin/env python3
"""Empirically determine each venue's trade `side` convention.

Blocker for the H1 re-run: Kraken documents `side` as the taker
(aggressor) direction; Coinbase's market_trades docs do not say. A wrong
assumption silently inverts a trade-sign autocorrelation, so the
convention is established from data here, Lee-Ready style:

    trade price >= prevailing ask  -> aggressor was a BUYER
    trade price <= prevailing bid  -> aggressor was a SELLER
    strictly inside the spread     -> unclassifiable at 1 s book cadence
                                      (reported, excluded; no tick-rule guess)

Timestamp basis: trades are taken at their EXCHANGE timestamp
(`trade_ts`) and sorted by it (Coinbase batches arrive with intra-batch
inversions); the prevailing quote is the same venue's most recent book
snapshot at-or-before that instant. Book snapshots carry only local
receive time — the measured receive-vs-exchange skew is ~50-90 ms,
small against the 1 s cadence, and is absorbed into the staleness
sensitivity. Trades whose freshest quote is older than MAX_QUOTE_AGE_S
are discarded as unjoinable.

Kraken serves as the control: its documented taker convention should
produce ~100% agreement. If it does not, the join/classifier is buggy
and the Coinbase number must not be trusted either.

Writes SIDE_CONVENTION.md (the file the H1 re-run must read) and prints
a summary table.
"""

from __future__ import annotations

import sys
from bisect import bisect_right
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from microstructure.ingest import _iter_jsonl_gz
from microstructure.venue import VENUE_SYMBOLS, VENUES, VenueBook, iter_venue_records

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DOC = ROOT / "SIDE_CONVENTION.md"

MAX_QUOTE_AGE_S = 2.0
AGE_BUCKETS = ((0.0, 0.5), (0.5, 1.0), (1.0, 2.0))
VERDICT_HI = 0.80  # pooled agreement >= this -> side == aggressor
VERDICT_LO = 0.20  # pooled agreement <= this -> side == maker (negate)
# The bands allow for Lee-Ready misclassification under 1 s quotes (the
# Kraken control measures that noise directly) while staying far from
# the ~50% coin-flip zone that would mean a broken join or useless field.


def classify(price: float, bid: float, ask: float) -> str | None:
    """Lee-Ready quote rule. Returns 'buy', 'sell', or None (inside spread)."""
    if price >= ask:
        return "buy"
    if price <= bid:
        return "sell"
    return None


def prevailing_quote(
    quote_ts: list[float],
    quotes: list[tuple[float, float]],
    ts: float,
    max_age_s: float = MAX_QUOTE_AGE_S,
) -> tuple[float, float, float] | None:
    """(bid, ask, age_s) from the most recent quote at-or-before ts, if fresh."""
    i = bisect_right(quote_ts, ts) - 1
    if i < 0:
        return None
    age = ts - quote_ts[i]
    if age > max_age_s:
        return None
    bid, ask = quotes[i]
    return bid, ask, age


def load_quotes(venue: str) -> dict[str, tuple[list[float], list[tuple[float, float]]]]:
    """symbol -> (sorted ts list, [(bid, ask)]) from the venue book capture."""
    acc: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
    for rec in iter_venue_records(DATA, venue):
        if isinstance(rec, VenueBook) and not rec.is_crossed:
            acc[rec.symbol].append((rec.ts, rec.best_bid, rec.best_ask))
    out: dict[str, tuple[list[float], list[tuple[float, float]]]] = {}
    for sym, rows in acc.items():
        rows.sort(key=lambda r: r[0])
        out[sym] = ([r[0] for r in rows], [(r[1], r[2]) for r in rows])
    return out


def load_trades(venue: str) -> dict[str, list[dict[str, object]]]:
    """symbol -> trades sorted by exchange timestamp."""
    out: dict[str, list[dict[str, object]]] = defaultdict(list)
    for path in sorted(DATA.glob(f"trades-{venue}-2*.jsonl.gz")):
        for obj in _iter_jsonl_gz(path):
            if obj.get("type") == "trade":
                out[str(obj["symbol"])].append(obj)
    for trades in out.values():
        trades.sort(key=lambda t: float(t["trade_ts"]))  # type: ignore[arg-type]
    return out


def main() -> int:
    doc = [
        "# SIDE_CONVENTION.md — empirically determined trade-side semantics",
        "",
        f"_Generated {datetime.now(UTC):%Y-%m-%d %H:%M} UTC by "
        "`scripts/validate_trade_side.py` from on-disk capture only._",
        "",
        "Method: Lee–Ready quote rule against the same venue's book capture "
        f"(quote at-or-before the trade's exchange ts, max age {MAX_QUOTE_AGE_S}s; "
        "trades strictly inside the spread are unclassifiable at 1 s cadence "
        "and excluded — their share is reported, not guessed).",
        "",
    ]
    print(f"{'venue':<9} {'symbol':<8} {'trades':>7} {'joined':>7} {'classif.':>8} "
          f"{'inside%':>8} {'agree':>7}")
    verdicts: dict[str, str] = {}
    for venue in VENUES:
        quotes = load_quotes(venue)
        trades = load_trades(venue)
        pooled_agree = 0
        pooled_n = 0
        age_stats = {b: [0, 0] for b in AGE_BUCKETS}  # bucket -> [agree, n]
        fresh_agree = [0, 0]  # <=1s quote age
        side_stats = {"buy": [0, 0], "sell": [0, 0]}  # recorded side -> [agree, n]
        doc += [f"## {venue}", "",
                "| symbol | trades | joined | classifiable | inside-spread "
                "| agreement (side == aggressor) |", "|---|---|---|---|---|---|"]
        for sym in VENUE_SYMBOLS:
            t_sym = trades.get(sym, [])
            q_ts, q_quotes = quotes.get(sym, ([], []))
            joined = 0
            classifiable = 0
            inside = 0
            agree = 0
            for t in t_sym:
                pq = prevailing_quote(q_ts, q_quotes, float(t["trade_ts"]))  # type: ignore[arg-type]
                if pq is None:
                    continue
                joined += 1
                bid, ask, age = pq
                aggressor = classify(float(t["price"]), bid, ask)  # type: ignore[arg-type]
                if aggressor is None:
                    inside += 1
                    continue
                classifiable += 1
                hit = aggressor == t["side"]
                agree += hit
                if t["side"] in side_stats:
                    side_stats[str(t["side"])][0] += hit
                    side_stats[str(t["side"])][1] += 1
                for b in AGE_BUCKETS:
                    if b[0] <= age < b[1]:
                        age_stats[b][0] += hit
                        age_stats[b][1] += 1
                if age <= 1.0:
                    fresh_agree[0] += hit
                    fresh_agree[1] += 1
            pooled_agree += agree
            pooled_n += classifiable
            rate = agree / classifiable if classifiable else float("nan")
            inside_share = inside / joined if joined else float("nan")
            print(f"{venue:<9} {sym:<8} {len(t_sym):>7,} {joined:>7,} "
                  f"{classifiable:>8,} {inside_share:>7.1%} {rate:>7.1%}")
            doc.append(
                f"| {sym} | {len(t_sym):,} | {joined:,} | {classifiable:,} "
                f"| {inside_share:.1%} | {rate:.1%} ({agree:,}/{classifiable:,}) |"
            )
        pooled_rate = pooled_agree / pooled_n if pooled_n else float("nan")
        if pooled_n >= 100 and pooled_rate >= VERDICT_HI:
            verdict = "side = AGGRESSOR (taker) — use as-is"
        elif pooled_n >= 100 and pooled_rate <= VERDICT_LO:
            verdict = "side = MAKER (resting) — NEGATE before use"
        else:
            verdict = "INCONCLUSIVE — do not use until resolved"
        verdicts[venue] = verdict
        weak = " **(weak: <100 classifiable trades)**" if pooled_n < 100 else ""
        doc += [
            "",
            f"**Pooled agreement: {pooled_rate:.2%} over {pooled_n:,} classifiable "
            f"trades.**{weak}",
            "",
            f"**Verdict: {verdict}**",
            "",
            "Quote-age sensitivity (agreement should not degrade much with age "
            "if the join is sound; sharp degradation would mean stale quotes "
            "are driving misclassification):",
            "",
            "| quote age | agreement | n |",
            "|---|---|---|",
        ]
        for b, (a, n) in age_stats.items():
            doc.append(
                f"| {b[0]:.1f}–{b[1]:.1f}s | {a / n:.1%} | {n:,} |"
                if n else f"| {b[0]:.1f}–{b[1]:.1f}s | – | 0 |"
            )
        if fresh_agree[1]:
            doc.append(
                f"\nRestricted to quotes ≤1 s old: "
                f"{fresh_agree[0] / fresh_agree[1]:.2%} ({fresh_agree[1]:,} trades)."
            )
        doc.append(
            "\nPer-side symmetry (a true convention inverts/agrees on BOTH "
            "recorded sides; asymmetry would mean something subtler): "
            + ", ".join(
                f"recorded {s}: {a / n:.1%} agreement over {n:,}"
                for s, (a, n) in side_stats.items()
                if n
            )
            + "."
        )
        doc.append("")
        print(f"{venue:<9} {'POOLED':<8} {'':>7} {'':>7} {pooled_n:>8,} "
              f"{'':>8} {pooled_rate:>7.2%}  -> {verdict}")

    doc += [
        "## Instructions for the H1 re-run",
        "",
        f"- **kraken**: {verdicts.get('kraken', '?')}",
        f"- **coinbase**: {verdicts.get('coinbase', '?')}",
        "",
        "## Confidence and limitations",
        "",
        "- Book cadence is 1 s: the prevailing quote can be up to ~1 s stale "
        "(plus ~50-90 ms receive-vs-exchange skew), which both misclassifies "
        "some fast-market trades and leaves inside-spread trades "
        "unclassifiable. The age-bucket tables above quantify the effect; a "
        "stable agreement rate across buckets means staleness is not driving "
        "the verdict.",
        "- Kraken is the control (documented taker convention): a high Kraken "
        "agreement validates the pipeline; the Coinbase verdict inherits that "
        "validation.",
        "- What would raise confidence further: more hours of trades (larger "
        "n per symbol), and event-driven book capture (sub-second quotes) to "
        "shrink the unclassifiable share.",
    ]
    OUT_DOC.write_text("\n".join(doc) + "\n")
    print(f"\nwrote {OUT_DOC.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
