#!/usr/bin/env python3
"""Backtest the imbalance strategy family against a random-strategy null.

For each symbol: 9 imbalance configs (threshold x holding period) and 50
random-strategy seeds. The deflated Sharpe of the best config accounts
for all 9 trials; the random fleet shows what luck alone produces in
this harness on this data.
"""

import itertools

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats as sps

from microstructure.analysis import (
    SYMBOLS,
    data_span_note,
    load_all_books,
    refresh_parquet,
    save_outputs,
)
from microstructure.backtest import (
    book_events,
    deflated_sharpe,
    imbalance_strategy,
    random_strategy,
    run_backtest,
)

THRESHOLDS = (0.3, 0.5, 0.7)
HOLDS = (10.0, 30.0, 60.0)
N_RANDOM = 50
SIZES = {"btcusdt": 0.002, "ethusdt": 0.05, "solusdt": 2.0}  # ~$100-130 clips


def main() -> None:
    refresh_parquet()
    books = load_all_books()

    fig, axes = plt.subplots(1, len(SYMBOLS), figsize=(5.5 * len(SYMBOLS), 4))
    rows = []
    for ax, sym in zip(axes, SYMBOLS, strict=True):
        book = books[sym]
        size = SIZES[sym]

        rand_sharpes = []
        for seed in range(N_RANDOM):
            r = run_backtest(book_events(book), random_strategy(seed, size=size))
            rand_sharpes.append(r.sharpe())
        rand_arr = np.asarray(rand_sharpes)

        trials = []
        for th, hold in itertools.product(THRESHOLDS, HOLDS):
            res = run_backtest(
                book_events(book), imbalance_strategy(threshold=th, size=size, hold_s=hold)
            )
            trials.append((th, hold, res))
            ax.plot(res.equity.index, res.equity.values, lw=0.7, alpha=0.6)

        best_th, best_hold, best = max(trials, key=lambda t: t[2].sharpe())
        r = best.returns
        per_bar_sr = float(r.mean() / r.std()) if len(r) > 1 and r.std() > 0 else 0.0
        trial_srs = []
        for _, _, res in trials:
            rr = res.returns
            trial_srs.append(float(rr.mean() / rr.std()) if rr.std() > 0 else 0.0)
        dsr = deflated_sharpe(
            per_bar_sr,
            n_obs=len(r),
            skew=float(sps.skew(r)),
            kurt=float(sps.kurtosis(r, fisher=False)),
            n_trials=len(trials),
            var_trial_sr=float(np.var(trial_srs)),
        )
        rows.append(
            f"| {sym.upper()} | {best_th}/{best_hold:.0f}s | {best.sharpe():+.2f} "
            f"| {dsr:.2f} | {best.n_trades} | ${best.fees_paid:.2f} "
            f"| {best.max_drawdown:.3%} | {rand_arr.mean():+.2f} ± {rand_arr.std():.2f} "
            f"| {np.percentile(rand_arr, 95):+.2f} |"
        )
        ax.set_title(f"{sym.upper()} — 9 imbalance configs ($10k start)")
        ax.tick_params(axis="x", labelsize=6)
    axes[0].set_ylabel("equity ($, marked to mid)")
    fig.tight_layout()

    md = "\n".join(
        [
            "# Backtest: imbalance strategy family vs random null",
            "",
            data_span_note(books),
            "",
            "Execution: taker-only, walk the displayed book, fills capped at "
            "displayed size, 10 bps taker fee per side, one-snapshot (~1 s) "
            "execution delay. Sharpe annualized from ~1 s bars.",
            "",
            "| symbol | best cfg (θ/hold) | ann. Sharpe | deflated SR (9 trials) "
            "| trades | fees | max DD | random null Sharpe (μ±σ, 50 seeds) | random p95 |",
            "|---|---|---|---|---|---|---|---|---|",
            *rows,
            "",
            "![chart](backtest.png)",
            "",
            "## What this data cannot support — read before believing any number",
            "",
            "- **Single venue.** Cross-venue arbitrage and venue-latency effects "
            "are invisible; Binance.US is a thin venue whose top of book may "
            "follow larger venues.",
            "- **1 s snapshots.** Everything between snapshots is unseen: "
            "queue dynamics, fleeting quotes, the actual sequence of trades vs "
            "book changes. Maker strategies are unmodelable — taker-only here.",
            "- **One overnight session.** A US-night, low-volatility regime. "
            "No daytime liquidity, no news, no weekend. Any parameter chosen "
            "on this night is fit to this night.",
            "- **Annualizing seconds-scale Sharpe** multiplies noise by ~5600; "
            "treat the column as a ranking statistic, not an expectation.",
            "- **Fees dominate.** At 10 bps/side a round trip costs ~20 bps "
            "while the BTC spread is ~2 bps; any high-frequency signal must "
            "clear fees, which is why the deflated SR column is the honest one.",
        ]
    )
    save_outputs("backtest", fig, md)


if __name__ == "__main__":
    main()
