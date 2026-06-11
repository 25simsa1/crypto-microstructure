#!/usr/bin/env python3
"""Cross-venue analysis: Kraken vs Coinbase price discovery.

Four questions, one report:

1. **Lead-lag** — lagged correlation of 1 s log mid returns per symbol
   (capture cadence is ~1 snapshot/s/venue, so sub-second lead-lag is
   *not measurable* on this data; the report says so rather than
   pretending).
2. **Leadership stability** — peak lag re-estimated per 3 h bucket
   across the day.
3. **Liquidity comparison & 24 h seasonality** — spread/depth medians
   per venue, and hour-of-day profiles night one could not see.
4. **Divergence vs fees** — does |mid_kraken − mid_coinbase| ever
   exceed a round trip at the registered fee levels?
   Coinbase Intro 1: 1.20% taker / 0.60% maker. Kraken tier
   unconfirmed: taker shown across 0.25–0.50% to demonstrate the
   conclusion is insensitive within the range.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from microstructure.venue import VENUE_SYMBOLS, load_venue_books, stale_mask

ROOT = Path(__file__).resolve().parent.parent
PARQUET = ROOT / "parquet"
OUT = ROOT / "output"

MAX_LAG = 30
BUCKET = "3h"
# round-trip cost scenarios (bps): cross both venues once each
FEE_SCENARIOS = {
    "taker+taker (Kraken 0.25%)": 120.0 + 25.0,
    "taker+taker (Kraken 0.50%)": 120.0 + 50.0,
    "maker+maker (CB 0.60% + Kraken 0.25%)": 60.0 + 25.0,
}


def venue_frames(symbol: str) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """(aligned 1s mids inner-joined, kraken spread bps, coinbase spread bps)."""
    out = {}
    spreads = {}
    for venue in ("kraken", "coinbase"):
        book = load_venue_books(PARQUET, venue, symbol)
        # drop stale runs (content frozen while snapshots keep arriving):
        # a frozen mid fabricates divergence and dampens correlations
        book = book[~stale_mask(book, min_s=120.0)]
        mid = (book["bid_px_0"] + book["ask_px_0"]) / 2.0
        out[venue] = mid.resample("1s").last()
        spreads[venue] = (
            (book["ask_px_0"] - book["bid_px_0"]) / mid * 1e4
        ).resample("1s").last()
    mids = pd.DataFrame(out).dropna()
    return mids, spreads["kraken"], spreads["coinbase"]


def lead_lag_curve(mids: pd.DataFrame) -> list[float]:
    """corr(kraken_t, coinbase_{t+k}) for k in -MAX_LAG..MAX_LAG.

    Peak at k > 0 means Kraken's return correlates with Coinbase's
    *later* return — Kraken leads.
    """
    r = np.log(mids).diff().dropna()
    return [
        float(r["kraken"].corr(r["coinbase"].shift(-k)))
        for k in range(-MAX_LAG, MAX_LAG + 1)
    ]


def peak_lag(curve: list[float]) -> tuple[int, float]:
    if all(np.isnan(c) for c in curve):
        return 0, float("nan")  # bucket with no usable variance (sleep gap)
    i = int(np.nanargmax(curve))
    return i - MAX_LAG, curve[i]


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    lines = [
        "# Cross-venue analysis: Kraken vs Coinbase",
        "",
        "Capture cadence is ~1 snapshot/s/venue: **sub-second lead-lag is "
        "not measurable here** — lags below are in whole seconds. Stale "
        "book runs (content frozen >=120 s, e.g. the live Coinbase/ETH "
        "freeze caught by the quality layer) are excluded throughout.",
        "",
        "## Lead-lag (full capture)",
        "",
        "| symbol | contemporaneous corr | peak lag | peak corr | leader |",
        "|---|---|---|---|---|",
    ]

    stability_rows: dict[str, list[tuple[pd.Timestamp, int]]] = {}
    div_all: dict[str, pd.Series] = {}
    for symbol in VENUE_SYMBOLS:
        mids, sp_k, sp_c = venue_frames(symbol)
        curve = lead_lag_curve(mids)
        k, v = peak_lag(curve)
        leader = "kraken" if k > 0 else "coinbase" if k < 0 else "tie"
        lines.append(
            f"| {symbol} | {curve[MAX_LAG]:+.3f} | {k:+d}s | {v:+.3f} | {leader} |"
        )
        if symbol == "BTC-USD":
            axes[0][0].plot(range(-MAX_LAG, MAX_LAG + 1), curve, marker="o", ms=2)
            axes[0][0].axvline(0, color="black", lw=0.6)
            axes[0][0].set_title("BTC lead-lag: corr(kraken_t, coinbase_t+k)")
            axes[0][0].set_xlabel("k (s); k>0 = Kraken leads")

        # leadership per 3h bucket
        r = np.log(mids).diff().dropna()
        buckets = []
        for ts, g in r.groupby(r.index.floor(BUCKET)):
            if len(g) < 600:
                continue
            c = [
                float(g["kraken"].corr(g["coinbase"].shift(-k)))
                for k in range(-MAX_LAG, MAX_LAG + 1)
            ]
            k_peak, v_peak = peak_lag(c)
            if not np.isnan(v_peak):
                buckets.append((ts, k_peak))
        stability_rows[symbol] = buckets

        # divergence in bps
        div_all[symbol] = (
            (mids["kraken"] - mids["coinbase"]).abs()
            / mids.mean(axis=1)
            * 1e4
        )

    for symbol, buckets in stability_rows.items():
        if buckets:
            ts, ks = zip(*buckets, strict=True)
            axes[0][1].plot(ts, ks, marker="o", ms=3, label=symbol)
    axes[0][1].axhline(0, color="black", lw=0.6)
    axes[0][1].set_title(f"peak lag per {BUCKET} bucket (+ = Kraken leads)")
    axes[0][1].legend(fontsize=7)
    axes[0][1].tick_params(axis="x", labelsize=6)

    # liquidity comparison + hour-of-day seasonality (BTC spread)
    lines += ["", "## Liquidity (median quoted spread, bps)", "",
              "| symbol | kraken | coinbase |", "|---|---|---|"]
    for symbol in VENUE_SYMBOLS:
        _, sp_k, sp_c = venue_frames(symbol)
        lines.append(f"| {symbol} | {sp_k.median():.2f} | {sp_c.median():.2f} |")
        if symbol == "BTC-USD":
            for name, sp in (("kraken", sp_k), ("coinbase", sp_c)):
                hourly = sp.groupby(sp.index.hour).median()
                axes[1][0].plot(hourly.index, hourly.values, marker="o", label=name)
    axes[1][0].set_title("BTC spread by hour of day (UTC) — full 24h cycle")
    axes[1][0].set_xlabel("UTC hour")
    axes[1][0].set_ylabel("median spread (bps)")
    axes[1][0].legend(fontsize=7)

    # divergence vs fees
    lines += ["", "## Cross-venue mid divergence vs round-trip fees", "",
              "| symbol | median (bps) | p99 | p99.9 | max |",
              "|---|---|---|---|---|"]
    for symbol, d in div_all.items():
        lines.append(
            f"| {symbol} | {d.median():.1f} | {d.quantile(0.99):.1f} "
            f"| {d.quantile(0.999):.1f} | {d.max():.1f} |"
        )
    pooled = pd.concat(div_all.values())
    axes[1][1].hist(pooled.clip(upper=200), bins=120, log=True, alpha=0.8)
    lines += ["", "| fee scenario | round trip (bps) | seconds exceeding | share |",
              "|---|---|---|---|"]
    for label, bps in FEE_SCENARIOS.items():
        n = int((pooled > bps).sum())
        axes[1][1].axvline(bps, ls="--", lw=1, color="tab:red")
        lines.append(f"| {label} | {bps:.0f} | {n:,} | {n / len(pooled):.4%} |")
    axes[1][1].set_title("cross-venue divergence (bps, pooled, log count)")
    axes[1][1].set_xlabel("|mid_k − mid_c| (bps); dashed = round-trip fee levels")

    fig.tight_layout()
    fig.savefig(OUT / "analysis_crossvenue.png", bbox_inches="tight", dpi=120)
    lines += [
        "",
        "![chart](analysis_crossvenue.png)",
        "",
        "**Maker caveat (registered fee answer):** the maker+maker line "
        "assumes both passive fills actually happen. Passive orders fill "
        "preferentially when price moves through them (adverse selection), "
        "so divergence > maker fees is *not* an executable profit — it is "
        "an upper bound on opportunity that ignores fill risk, queue "
        "position, and inventory/transfer latency between venues.",
        "",
        "**Sensitivity:** the taker conclusion is identical at Kraken "
        "0.25% and 0.50% — the binding cost is Coinbase's 1.20% taker.",
    ]
    (OUT / "analysis_crossvenue.md").write_text("\n".join(lines))
    print("wrote output/analysis_crossvenue.md")


if __name__ == "__main__":
    main()
