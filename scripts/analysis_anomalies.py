#!/usr/bin/env python3
"""Flag anomalies in the night's book stream and chart them in context.

Episodes come from trailing-robust detectors (median + MAD, past-only):
spread spikes, near-touch depth evaporation, vol regime shifts.
"""

import matplotlib.pyplot as plt

from microstructure import features as F
from microstructure.analysis import (
    data_span_note,
    load_all_books,
    refresh_parquet,
    save_outputs,
)
from microstructure.anomaly import detect_all

COLORS = {"spread_spike": "tab:red", "depth_evaporation": "tab:purple", "vol_shift": "tab:orange"}


def main() -> None:
    refresh_parquet()
    books = load_all_books()

    fig, axes = plt.subplots(len(books), 1, figsize=(11, 3 * len(books)), sharex=True)
    rows = []
    total = 0
    for ax, (sym, book) in zip(axes, books.items(), strict=True):
        spread = F.spread_bps(book).resample("5s").median()
        ax.plot(spread.index, spread.values, lw=0.7, color="tab:blue")
        ax.set_ylabel(f"{sym.upper()} spread (bps)")
        ax.set_yscale("log")
        episodes = detect_all(book)
        total += len(episodes)
        for e in episodes:
            ax.axvspan(e.start, e.end, color=COLORS[e.kind], alpha=0.35)
            rows.append(
                f"| {sym.upper()} | {e.kind} | {e.start:%H:%M:%S} | {e.duration_s:.0f}s "
                f"| {e.peak:.3g} | {e.baseline:.3g} |"
            )
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.5) for c in COLORS.values()]
    axes[0].legend(handles, list(COLORS), fontsize=7)
    axes[-1].set_xlabel("UTC")
    fig.suptitle("Anomaly episodes over the quoted spread")
    fig.tight_layout()

    if not rows:
        rows = ["| – | none detected | – | – | – | – |"]
    md = "\n".join(
        [
            "# Anomaly episodes",
            "",
            data_span_note(books),
            "",
            "Detectors use trailing median + MAD only (no future data). "
            "Spread spikes: >4x the trailing 15-min median for 3s+. Depth evaporation: "
            "<15% of trailing median within ±10 bps for 3s+. Vol shifts: 1-min RV "
            ">6 MADs over 30 min.",
            "",
            "| symbol | kind | start (UTC) | duration | peak | baseline |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
            f"**{total} episode(s) detected.**",
            "",
            "![chart](analysis_anomalies.png)",
        ]
    )
    save_outputs("analysis_anomalies", fig, md)


if __name__ == "__main__":
    main()
