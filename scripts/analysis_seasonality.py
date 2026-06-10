#!/usr/bin/env python3
"""Intraday seasonality of spread and depth.

Buckets quoted spread (bps) and near-touch depth ($ within 10 bps of mid)
into 15-minute time-of-day bins per symbol. With a single night of data
this shows the *overnight liquidity profile*, not true seasonality —
the markdown is explicit about that.
"""

import matplotlib.pyplot as plt

from microstructure import features as F
from microstructure.analysis import (
    data_span_note,
    load_all_books,
    refresh_parquet,
    save_outputs,
)


def main() -> None:
    refresh_parquet()
    books = load_all_books()

    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    lines = []
    for sym, book in books.items():
        spread = F.spread_bps(book)
        depth = F.depth_notional(book, "bid", 10) + F.depth_notional(book, "ask", 10)
        bucket = spread.index.floor("15min")
        sp = spread.groupby(bucket).median()
        dp = depth.groupby(bucket).median()
        axes[0].plot(sp.index, sp.values, marker="o", ms=3, label=sym.upper())
        axes[1].plot(dp.index, dp.values, marker="o", ms=3, label=sym.upper())
        lines.append(
            f"| {sym.upper()} | {spread.median():.2f} | {sp.max() / sp.min():.2f}x "
            f"| ${depth.median():,.0f} | {dp.max() / dp.min():.2f}x |"
        )
    axes[0].set_ylabel("median quoted spread (bps)")
    axes[0].set_yscale("log")
    axes[0].legend()
    axes[1].set_ylabel("median depth within ±10 bps ($)")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("UTC time (15-min buckets)")
    fig.suptitle("Overnight liquidity profile: spread and near-touch depth")
    fig.autofmt_xdate()

    md = "\n".join(
        [
            "# Intraday liquidity profile",
            "",
            data_span_note(books),
            "",
            "| symbol | median spread (bps) | spread max/min across buckets "
            "| median depth ±10bps | depth max/min |",
            "|---|---|---|---|---|",
            *lines,
            "",
            "![chart](analysis_seasonality.png)",
            "",
            "**Caveat:** one night of data shows the overnight *profile*, not "
            "recurring seasonality — that claim needs multiple days so each "
            "time-of-day bucket has independent observations.",
        ]
    )
    save_outputs("analysis_seasonality", fig, md)


if __name__ == "__main__":
    main()
