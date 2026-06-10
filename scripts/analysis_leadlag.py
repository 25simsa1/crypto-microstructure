#!/usr/bin/env python3
"""Cross-asset lead-lag between BTC, ETH and SOL.

Cross-correlation of 1 s log mid returns at lags −30..+30 s for each
pair. A peak at positive lag k for pair (A, B) means A's returns
correlate with B's returns k seconds *later* — A leads B. The ±2/√N
band is the approximate 95% null interval for white noise.
"""

import itertools

import matplotlib.pyplot as plt
import numpy as np

from microstructure.analysis import (
    aligned_mids,
    data_span_note,
    load_all_books,
    refresh_parquet,
    save_outputs,
)

MAX_LAG = 30


def main() -> None:
    refresh_parquet()
    books = load_all_books()
    rets = np.log(aligned_mids(books, "1s")).diff().dropna()

    pairs = list(itertools.combinations(rets.columns, 2))
    fig, axes = plt.subplots(1, len(pairs), figsize=(5 * len(pairs), 4), sharey=True)
    lines = []
    for ax, (a, b) in zip(axes, pairs, strict=True):
        lags = range(-MAX_LAG, MAX_LAG + 1)
        cc = [rets[a].corr(rets[b].shift(-k)) for k in lags]
        n = len(rets)
        band = 2 / np.sqrt(n)
        ax.bar(list(lags), cc, width=0.9)
        ax.axhspan(-band, band, color="gray", alpha=0.25, label="±2/√N null band")
        ax.axvline(0, color="black", lw=0.6)
        ax.set_title(f"{a.upper()} vs {b.upper()}")
        ax.set_xlabel(f"lag k (s): k>0 ⇒ {a.upper()} leads")
        peak_k = list(lags)[int(np.nanargmax(np.abs(cc)))]
        peak_v = cc[int(np.nanargmax(np.abs(cc)))]
        contemp = cc[MAX_LAG]
        lines.append(
            f"| {a.upper()}/{b.upper()} | {contemp:+.3f} | {peak_k:+d}s | "
            f"{peak_v:+.3f} | {band:.3f} |"
        )
    axes[0].set_ylabel("corr of 1s log returns")
    fig.suptitle("Lead-lag cross-correlograms")
    fig.tight_layout()

    md = "\n".join(
        [
            "# Cross-asset lead-lag",
            "",
            data_span_note(books),
            "",
            "| pair | contemporaneous corr | peak lag | peak corr | 95% null band |",
            "|---|---|---|---|---|",
            *lines,
            "",
            "![chart](analysis_leadlag.png)",
            "",
            "**Caveats:** 1 s last-observation sampling induces spurious lead-lag "
            "(Epps effect / asynchronous trading): the less active symbol's mid "
            "updates later, which *looks* like following. A peak at ±1 s within "
            "the null band is noise, not alpha. Single venue — cross-venue "
            "latency arbitrage is invisible here.",
        ]
    )
    save_outputs("analysis_leadlag", fig, md)


if __name__ == "__main__":
    main()
