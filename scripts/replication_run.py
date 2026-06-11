#!/usr/bin/env python3
"""Execute the pre-registered replication plan in REPLICATION.md.

The procedure here is the frozen one — any change to the statistics
computed below without a new registration is a protocol violation.
Outputs: output/replication_results.md (+ PNG of the Epps curves).
"""

from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox

from microstructure.venue import VENUES, load_venue_books, stale_mask

ROOT = Path(__file__).resolve().parent.parent
PARQUET = ROOT / "parquet"
OUT = ROOT / "output"

# frozen window: night one's capture hours, next day (UTC)
W_START = datetime(2026, 6, 11, 8, 3, tzinfo=UTC)
W_END = datetime(2026, 6, 11, 13, 34, tzinfo=UTC)
EPPS_INTERVALS = ("1s", "2s", "5s", "10s", "30s", "60s", "120s", "300s")
VOID_COVERAGE = 0.70

# night-one benchmarks, copied from REPLICATION.md
BENCH_H2 = {"SOL-USD": -0.0143, "ETH-USD": -0.0172, "BTC-USD": +0.0005}
BENCH_H3 = (0.345, 0.928)


def mid_1s(book: pd.DataFrame) -> pd.Series:
    return ((book["bid_px_0"] + book["ask_px_0"]) / 2.0).resample("1s").last()


def window_coverage(book: pd.DataFrame) -> float:
    """Fraction of 1 s slots in the frozen window that have a snapshot."""
    w = book.loc[W_START:W_END]
    if w.empty:
        return 0.0
    slots = int((W_END - W_START).total_seconds())
    return float(mid_1s(w).notna().sum()) / slots


def tick_sign_stats(mid: pd.Series) -> tuple[float, float, int]:
    """Frozen H2 procedure: mean ACF(1-5) and LB(10) p on nonzero tick signs."""
    d = mid.diff().dropna()
    signs = np.sign(d[d != 0])
    if len(signs) < 50:
        return float("nan"), float("nan"), len(signs)
    acf = float(np.mean([signs.autocorr(lag=k) for k in range(1, 6)]))
    lb = float(acorr_ljungbox(signs, lags=[10], return_df=True)["lb_pvalue"].iloc[0])
    return acf, lb, len(signs)


def epps_curve(btc: pd.Series, eth: pd.Series) -> list[float]:
    """Frozen H3 procedure: corr of log returns at each sampling interval."""
    df = pd.DataFrame({"btc": btc, "eth": eth})
    out = []
    for interval in EPPS_INTERVALS:
        r = np.log(df.resample(interval).last()).diff().dropna()
        out.append(float(r["btc"].corr(r["eth"])))
    return out


def main() -> None:
    lines = [
        "# Replication results (pre-registered: see REPLICATION.md)",
        "",
        f"Matched window: {W_START:%Y-%m-%d %H:%M} → {W_END:%H:%M} UTC. "
        "H1 (trade-sign memory) is NOT TESTABLE on this capture (book-only); "
        "registered as a capture-design finding.",
        "",
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)

    verdicts: dict[str, dict[str, str]] = {v: {} for v in VENUES}
    for ax, venue in zip(axes, VENUES, strict=True):
        books = {s: load_venue_books(PARQUET, venue, s) for s in BENCH_H2}
        cov = {s: window_coverage(b) for s, b in books.items()}
        voided = {s: c < VOID_COVERAGE for s, c in cov.items()}

        lines += [f"## {venue}", "",
                  "| symbol | window coverage | void? |", "|---|---|---|"]
        lines += [
            f"| {s} | {cov[s]:.1%} | {'VOID (<70%)' if voided[s] else 'ok'} |"
            for s in sorted(cov)
        ]
        lines.append("")

        # --- H2: tick-sign memory, matched window then full capture
        lines += [
            "| H2 tick-sign | window | ACF(1-5) | LB p | n ticks "
            "| night-1 bench | verdict |",
            "|---|---|---|---|---|---|---|",
        ]
        for sym in ("SOL-USD", "ETH-USD", "BTC-USD"):
            for label, frame in (
                ("matched", books[sym].loc[W_START:W_END]),
                ("full-day", books[sym]),
            ):
                acf, lb, n = tick_sign_stats(mid_1s(frame))
                if sym == "BTC-USD":
                    verdict = "descriptive"
                elif label == "full-day":
                    verdict = "descriptive (robustness)"
                elif voided[sym]:
                    verdict = "VOID"
                elif np.isnan(acf):
                    verdict = "VOID (too few ticks)"
                elif acf < 0 and lb < 1e-3:
                    verdict = "REPLICATED"
                elif acf > 0 and lb < 1e-3:
                    verdict = "SIGN FLIP"
                else:
                    verdict = "not significant"
                if sym != "BTC-USD" and label == "matched":
                    verdicts[venue][sym] = verdict
                lines.append(
                    f"| {sym} | {label} | {acf:+.4f} | {lb:.2e} | {n:,} "
                    f"| {BENCH_H2[sym]:+.4f} | {verdict} |"
                )
        lines.append("")

        # --- H3: Epps
        w = {s: mid_1s(books[s].loc[W_START:W_END]) for s in ("BTC-USD", "ETH-USD")}
        curve = epps_curve(w["BTC-USD"], w["ETH-USD"])
        rise = curve[-1] - curve[0]
        h3_void = voided["BTC-USD"] or voided["ETH-USD"]
        h3 = (
            "VOID"
            if h3_void
            else "REPLICATED"
            if (rise >= 0.30 and curve[-1] >= 0.70)
            else "FAILED"
        )
        verdicts[venue]["epps"] = h3
        lines += [
            f"**H3 Epps (BTC/ETH, matched window):** corr {curve[0]:+.3f} @ 1s → "
            f"{curve[-1]:+.3f} @ 300s (rise {rise:+.3f}; night-1: "
            f"{BENCH_H3[0]:+.3f} → {BENCH_H3[1]:+.3f}). **{h3}**",
            "",
        ]
        xs = [float(i.rstrip("s")) for i in EPPS_INTERVALS]
        ax.plot(xs, curve, marker="o", label=f"{venue} night 2")
        ax.plot(xs, [BENCH_H3[0], *[np.nan] * 6, BENCH_H3[1]], "k*", ms=10,
                label="night-1 endpoints")
        ax.set_xscale("log")
        ax.set_title(f"Epps re-test: {venue}")
        ax.set_xlabel("sampling interval (s)")
        ax.legend(fontsize=7)
    axes[0].set_ylabel("corr(BTC, ETH) log returns")
    fig.tight_layout()
    fig.savefig(OUT / "replication_epps.png", bbox_inches="tight", dpi=120)

    lines += ["## Verdict summary (matched window, per registration)", ""]
    for venue in VENUES:
        lines.append(
            f"- **{venue}**: SOL {verdicts[venue].get('SOL-USD', '?')}, "
            f"ETH {verdicts[venue].get('ETH-USD', '?')}, "
            f"Epps {verdicts[venue].get('epps', '?')}"
        )
    # ------------------------------------------------------------------
    # POST-HOC sensitivity (NOT registered): the quality layer later found
    # stale-book episodes (content frozen while snapshots arrive) inside
    # the matched window on Coinbase. The registered coverage check counts
    # frozen snapshots as data, so the verdicts above stand by the letter
    # of the registration; this section reports what changes when stale
    # runs are excluded and coverage counts only FRESH seconds.
    # ------------------------------------------------------------------
    lines += [
        "## POST-HOC sensitivity: stale-book exclusion (not registered)",
        "",
        "Frozen-book episodes were discovered after the registered run "
        "(see venue_quality.md). Same frozen procedure, stale runs "
        "(>=120 s unchanged top-of-book with snapshots arriving) excluded:",
        "",
        "| venue | symbol | fresh coverage | ACF(1-5) | LB p | n ticks "
        "| registered verdict | sensitivity verdict |",
        "|---|---|---|---|---|---|---|---|",
    ]
    slots = int((W_END - W_START).total_seconds())
    for venue in VENUES:
        for sym in ("SOL-USD", "ETH-USD"):
            book = load_venue_books(PARQUET, venue, sym)
            fresh = book[~stale_mask(book, min_s=120.0)]
            wfresh = fresh.loc[W_START:W_END]
            fresh_cov = float(mid_1s(wfresh).notna().sum()) / slots if len(wfresh) else 0.0
            acf, lb, n = tick_sign_stats(mid_1s(wfresh))
            if fresh_cov < VOID_COVERAGE:
                sens = "VOID (fresh coverage < 70%)"
            elif np.isnan(acf):
                sens = "VOID (too few ticks)"
            elif acf < 0 and lb < 1e-3:
                sens = "REPLICATED"
            elif acf > 0 and lb < 1e-3:
                sens = "SIGN FLIP"
            else:
                sens = "not significant"
            lines.append(
                f"| {venue} | {sym} | {fresh_cov:.1%} | {acf:+.4f} | {lb:.2e} "
                f"| {n:,} | {verdicts[venue].get(sym, '?')} | {sens} |"
            )
    lines += [
        "",
        "Stale runs emit zero mid ticks, so they dilute n rather than "
        "fabricate signs; agreement between the two columns means the "
        "registered verdicts were not artifacts of staleness.",
        "",
        "![epps](replication_epps.png)",
        "",
        "_Cross-venue caveat (registered): pass = venue-robust regularity; "
        "fail = ambiguous between night-one noise and venue heterogeneity._",
    ]
    (OUT / "replication_results.md").write_text("\n".join(lines))
    print("wrote output/replication_results.md")
    for venue in VENUES:
        print(f"  {venue}: {verdicts[venue]}")


if __name__ == "__main__":
    main()
