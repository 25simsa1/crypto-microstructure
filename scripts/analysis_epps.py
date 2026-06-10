#!/usr/bin/env python3
"""The Epps effect: cross-asset correlation vs sampling frequency.

Epps (1979): return correlations between related assets shrink as the
sampling interval shrinks, because price updates are asynchronous —
at 1 s, one asset's mid often simply hasn't reacted yet. Plotting
pairwise correlation against the sampling interval (1 s … 5 min) shows
where correlation 'saturates': the timescale below which comovement
information is mostly noise on this venue.
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

INTERVALS = ("1s", "2s", "5s", "10s", "30s", "60s", "120s", "300s")


def main() -> None:
    refresh_parquet()
    books = load_all_books()

    pairs = list(itertools.combinations(sorted(books), 2))
    curves: dict[tuple[str, str], list[float]] = {p: [] for p in pairs}
    ns: list[int] = []
    for interval in INTERVALS:
        rets = np.log(aligned_mids(books, interval)).diff().dropna()
        ns.append(len(rets))
        for a, b in pairs:
            curves[(a, b)].append(float(rets[a].corr(rets[b])))

    fig, ax = plt.subplots(figsize=(8, 5))
    x = [float(i.rstrip("s")) for i in INTERVALS]
    rows = []
    for (a, b), ys in curves.items():
        ax.plot(x, ys, marker="o", label=f"{a.upper()}/{b.upper()}")
        sat = ys[-1]
        half_idx = next((i for i, y in enumerate(ys) if sat != 0 and y >= 0.5 * sat), None)
        half = f"{x[half_idx]:g}s" if half_idx is not None else "n/a"
        rows.append(f"| {a.upper()}/{b.upper()} | {ys[0]:+.3f} | {sat:+.3f} | {half} |")
    ax.set_xscale("log")
    ax.set_xlabel("sampling interval (s, log scale)")
    ax.set_ylabel("correlation of log returns")
    ax.set_title("Epps effect: correlation vs sampling frequency")
    ax.legend()

    md = "\n".join(
        [
            "# Epps effect",
            "",
            data_span_note(books),
            "",
            "| pair | corr @ 1s | corr @ 300s | interval reaching half of 300s corr |",
            "|---|---|---|---|",
            *rows,
            "",
            f"Observations per interval: {ns[0]:,} at 1s down to {ns[-1]:,} at 300s.",
            "",
            "![chart](analysis_epps.png)",
            "",
            "**Read:** correlation rising with the sampling interval is the "
            "classic Epps signature of asynchronous price updates. The "
            "saturation timescale bounds how fast cross-asset information "
            "propagates *on this venue*. The 300 s points rest on few "
            "observations overnight — widest error bars on the right.",
        ]
    )
    save_outputs("analysis_epps", fig, md)


if __name__ == "__main__":
    main()
