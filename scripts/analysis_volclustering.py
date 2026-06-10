#!/usr/bin/env python3
"""Volatility clustering and jump detection.

Per symbol: 1-min realized variance autocorrelation with Ljung–Box
significance, and realized variance vs bipower variation (their gap
estimates the jump component of variance).
"""

import matplotlib.pyplot as plt
import numpy as np
from statsmodels.stats.diagnostic import acorr_ljungbox

from microstructure import features as F
from microstructure.analysis import (
    data_span_note,
    load_all_books,
    refresh_parquet,
    save_outputs,
)

N_ACF_LAGS = 20


def main() -> None:
    refresh_parquet()
    books = load_all_books()

    fig, axes = plt.subplots(2, len(books), figsize=(5 * len(books), 7))
    lines = []
    for col, (sym, book) in enumerate(books.items()):
        mid = F.mid(book)
        rv = F.realized_variance(mid, "1min").dropna()
        bv = F.bipower_variation(mid, "1min").dropna()

        acf = [rv.autocorr(lag=k) for k in range(1, N_ACF_LAGS + 1)]
        band = 2 / np.sqrt(len(rv))
        lb = acorr_ljungbox(rv, lags=[10], return_df=True)
        lb_p = float(lb["lb_pvalue"].iloc[0])

        ax = axes[0][col]
        ax.bar(range(1, N_ACF_LAGS + 1), acf)
        ax.axhspan(-band, band, color="gray", alpha=0.25)
        ax.set_title(f"{sym.upper()} RV(1min) autocorrelation")
        ax.set_xlabel("lag (min)")

        ax = axes[1][col]
        vol_rv = F.annualize_variance(rv, 60) * 100
        vol_bv = F.annualize_variance(bv.reindex(rv.index), 60) * 100
        ax.plot(vol_rv.index, vol_rv.values, label="RV vol", lw=0.9)
        ax.plot(vol_bv.index, vol_bv.values, label="bipower vol", lw=0.9)
        ax.set_title("annualized vol (%), 1-min bars")
        ax.legend(fontsize=7)
        ax.tick_params(axis="x", labelsize=6)

        jump_share = float(((rv - bv.reindex(rv.index)).clip(lower=0).sum()) / rv.sum())
        lines.append(
            f"| {sym.upper()} | {float(np.mean(acf[:5])):+.3f} | {lb_p:.2g} "
            f"| {vol_rv.median():.1f}% | {jump_share:.1%} |"
        )
    fig.tight_layout()

    md = "\n".join(
        [
            "# Volatility clustering and jumps",
            "",
            data_span_note(books),
            "",
            "| symbol | mean ACF lags 1-5 | Ljung-Box p (10 lags) | median ann. vol "
            "| jump share of variance |",
            "|---|---|---|---|---|",
            *lines,
            "",
            "![chart](analysis_volclustering.png)",
            "",
            "A small Ljung–Box p-value rejects 'RV is white noise' — the "
            "signature of volatility clustering. Jump share is "
            "max(RV − BV, 0)/RV summed over bars: bipower variation is "
            "jump-robust, so the excess of RV over BV estimates the "
            "discontinuous part. With one quiet overnight session, treat "
            "both as descriptive, not structural.",
        ]
    )
    save_outputs("analysis_volclustering", fig, md)


if __name__ == "__main__":
    main()
