#!/usr/bin/env python3
"""Trade-tape analysis: effective spread, sign memory, volume clock.

Three views per symbol:

* **Effective vs quoted spread** — do trades print inside the touch?
* **Trade-sign autocorrelation** — order-flow memory (Lillo & Farmer:
  slow decay from sliced parent orders).
* **Volume bars** — net signed volume per equal-volume bar vs that
  bar's return: the crudest possible price-impact picture.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox

from microstructure import features as F
from microstructure.analysis import (
    PARQUET_DIR,
    data_span_note,
    load_all_books,
    refresh_parquet,
    save_outputs,
)
from microstructure.parquet import load_trades

MAX_LAG = 20


def runs_test_z(signs: pd.Series) -> float:
    """Wald–Wolfowitz runs test on the +/- sign sequence.

    z < 0 means fewer runs than chance (persistence / order-flow
    memory); z > 0 means alternation. |z| > 1.96 ~ 5% two-sided.
    """
    s = signs[signs != 0].to_numpy()
    n_pos = int((s > 0).sum())
    n_neg = int((s < 0).sum())
    n = n_pos + n_neg
    if n_pos == 0 or n_neg == 0 or n < 3:
        return float("nan")
    runs = 1 + int((s[1:] != s[:-1]).sum())
    mean = 2.0 * n_pos * n_neg / n + 1.0
    var = (mean - 1.0) * (mean - 2.0) / (n - 1.0)
    return float((runs - mean) / np.sqrt(var)) if var > 0 else float("nan")


def main() -> None:
    refresh_parquet()
    books = load_all_books()

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    rows = []
    impact_pts: list[tuple[float, float]] = []
    for sym, book in books.items():
        trades = load_trades(PARQUET_DIR, sym)
        mid = F.mid(book)
        es = F.effective_spread_bps(trades, mid)
        qs = F.spread_bps(book)
        acf = F.trade_sign_autocorr(trades, max_lag=MAX_LAG)
        axes[0].plot(acf.index, acf.values, marker="o", ms=3, label=sym.upper())

        # volume bars sized to ~10 median trades per bar
        bucket = float(trades["qty"].median() * 10)
        bars = F.volume_bars(trades, bucket)
        if len(bars) >= 3:
            ret_bps = (bars["close"] / bars["open"] - 1.0) * 1e4
            norm_flow = bars["net_signed_qty"] / bucket
            impact_pts += list(zip(norm_flow, ret_bps, strict=True))
            axes[2].scatter(norm_flow, ret_bps, s=18, alpha=0.7, label=sym.upper())
        buy_share = float((trades["signed_qty"] > 0).mean())
        signs = np.sign(trades["signed_qty"])
        lb_p = float(acorr_ljungbox(signs, lags=[10], return_df=True)["lb_pvalue"].iloc[0])
        rz = runs_test_z(signs)
        rows.append(
            f"| {sym.upper()} | {len(trades):,} | {buy_share:.0%} | "
            f"{es.median():.2f} | {qs.median():.2f} | "
            f"{float(acf.iloc[:5].mean()):+.3f} | {lb_p:.3f} | {rz:+.2f} | {len(bars)} |"
        )

    band_n = min(len(load_trades(PARQUET_DIR, s)) for s in books)
    axes[0].axhspan(-2 / np.sqrt(band_n), 2 / np.sqrt(band_n), color="gray", alpha=0.25)
    axes[0].axhline(0, color="black", lw=0.6)
    axes[0].set_title("trade-sign autocorrelation")
    axes[0].set_xlabel("lag (trades)")
    axes[0].legend(fontsize=7)

    # effective vs quoted spread distributions, pooled view
    for sym, book in books.items():
        trades = load_trades(PARQUET_DIR, sym)
        es = F.effective_spread_bps(trades, F.mid(book))
        axes[1].hist(es.clip(upper=12), bins=30, alpha=0.5, label=f"{sym.upper()} eff")
    axes[1].set_title("effective spread per trade (bps, clipped at 12)")
    axes[1].set_xlabel("bps")
    axes[1].legend(fontsize=7)

    axes[2].axhline(0, color="black", lw=0.6)
    axes[2].axvline(0, color="black", lw=0.6)
    axes[2].set_title("volume-bar net flow vs bar return")
    axes[2].set_xlabel("net signed qty / bucket")
    axes[2].set_ylabel("bar return (bps)")
    axes[2].legend(fontsize=7)
    fig.tight_layout()

    if impact_pts:
        xs = np.array([p[0] for p in impact_pts])
        ys = np.array([p[1] for p in impact_pts])
        impact_corr = float(np.corrcoef(xs, ys)[0, 1]) if len(xs) > 2 else float("nan")
    else:
        impact_corr = float("nan")

    md = "\n".join(
        [
            "# Trade-tape analysis",
            "",
            data_span_note(books),
            "",
            "| symbol | trades | buy share | median eff spread (bps) "
            "| median quoted (bps) | sign ACF lags 1-5 | LB p (10 lags) "
            "| runs z | volume bars |",
            "|---|---|---|---|---|---|---|---|---|",
            *rows,
            "",
            f"Pooled corr(net flow, bar return) across symbols: **{impact_corr:+.2f}**.",
            "",
            "![chart](analysis_tape.png)",
            "",
            "**Significance:** Ljung–Box (10 lags) tests 'signs are white "
            "noise'; the runs test z is negative under persistence. Both "
            "are joint with the thin-tape caveat below — a p of 0.04 on "
            "one night and one venue is a hint, not a finding.",
            "",
            "**Caveats:** the overnight tape is thin (hundreds of trades, not "
            "thousands), so sign-ACF confidence bands are wide and the "
            "flow/return scatter is descriptive only. Effective spread uses "
            "the 1 s book mid as the benchmark — staleness up to 1 s biases "
            "it upward when the market moves between snapshot and trade.",
        ]
    )
    save_outputs("analysis_tape", fig, md)


if __name__ == "__main__":
    main()
