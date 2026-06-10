#!/usr/bin/env python3
"""Does book pressure predict short-horizon mid moves?

Features, all computed from data at or before t (no lookahead):
  * imb5   — book imbalance over top 5 levels
  * ofi10  — 10 s rolling sum of best-level order flow imbalance
  * mprem  — microprice premium over mid, bps

Target: forward log mid return over h ∈ {5, 30, 60} s, sampled on a 1 s grid.

Method: chronological 70/30 train/test split. On train, univariate OLS
with Newey–West (HAC) errors, lags = horizon (overlapping forward
returns are serially correlated by construction — plain OLS t-stats
would be inflated). On test: out-of-sample Pearson correlation and
direction hit rate. 27 hypotheses are tested, so the markdown applies a
Bonferroni-adjusted significance threshold.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from microstructure import features as F
from microstructure.analysis import (
    data_span_note,
    load_all_books,
    refresh_parquet,
    save_outputs,
)

HORIZONS = (5, 30, 60)
N_TESTS = 27  # 3 symbols x 3 features x 3 horizons
ALPHA = 0.05


def build_frame(book: pd.DataFrame) -> pd.DataFrame:
    """1 s grid of features (info ≤ t) and forward returns (info > t)."""
    mid = F.mid(book).resample("1s").last()
    feats = pd.DataFrame(
        {
            "imb5": F.imbalance(book, levels=5).resample("1s").last(),
            "ofi10": F.ofi(book).resample("1s").sum(min_count=1).rolling(10).sum(),
            "mprem": ((F.microprice(book) - F.mid(book)) / F.mid(book) * 1e4)
            .resample("1s")
            .last(),
        }
    )
    for h in HORIZONS:
        feats[f"fwd{h}"] = np.log(mid.shift(-h)) - np.log(mid)
    return feats.dropna()


def main() -> None:
    refresh_parquet()
    books = load_all_books()

    rows = []
    results: dict[tuple[str, str, int], dict[str, float]] = {}
    for sym, book in books.items():
        df = build_frame(book)
        cut = int(len(df) * 0.7)
        train, test = df.iloc[:cut], df.iloc[cut:]
        for feat in ("imb5", "ofi10", "mprem"):
            for h in HORIZONS:
                y, x = train[f"fwd{h}"], sm.add_constant(train[feat])
                fit = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": h})
                tstat = float(fit.tvalues[feat])
                oos_corr = float(test[feat].corr(test[f"fwd{h}"]))
                nz = test[test[f"fwd{h}"] != 0]
                hit = float((np.sign(nz[feat]) == np.sign(nz[f"fwd{h}"])).mean())
                results[(sym, feat, h)] = {"t": tstat, "oos": oos_corr, "hit": hit}
                rows.append(
                    f"| {sym.upper()} | {feat} | {h}s | {tstat:+.2f} "
                    f"| {oos_corr:+.3f} | {hit:.1%} | {len(test):,} |"
                )

    # chart: OOS correlation bars + decile plot for the strongest train-t combo
    best = max(results, key=lambda k: abs(results[k]["t"]))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    labels = [f"{s[:3]}/{f}/{h}s" for (s, f, h) in results]
    vals = [results[k]["oos"] for k in results]
    colors = ["tab:blue" if v > 0 else "tab:red" for v in vals]
    axes[0].bar(range(len(vals)), vals, color=colors)
    axes[0].set_xticks(range(len(labels)), labels, rotation=90, fontsize=6)
    axes[0].set_ylabel("out-of-sample corr(feature, fwd return)")
    axes[0].set_title("OOS correlation, all symbol/feature/horizon combos")

    sym, feat, h = best
    df = build_frame(books[sym])
    cut = int(len(df) * 0.7)
    train, test = df.iloc[:cut], df.iloc[cut:]
    edges = np.quantile(train[feat], np.linspace(0, 1, 11))
    bins = pd.cut(test[feat], np.unique(edges), include_lowest=True)
    dec = test.groupby(bins, observed=True)[f"fwd{h}"].mean() * 1e4
    axes[1].plot(range(len(dec)), dec.values, marker="o")
    axes[1].axhline(0, color="gray", lw=0.8)
    axes[1].set_xlabel(f"{feat} decile (edges fit on train)")
    axes[1].set_ylabel(f"mean fwd {h}s return (bps), test set")
    axes[1].set_title(f"strongest combo: {sym.upper()} {feat} @ {h}s")
    fig.tight_layout()

    bonferroni_t = 3.58  # two-sided z for alpha=0.05/27
    md = "\n".join(
        [
            "# Book pressure vs short-horizon returns",
            "",
            data_span_note(books),
            "",
            f"Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. "
            f"**{N_TESTS} hypotheses tested → Bonferroni threshold |t| > {bonferroni_t}** "
            f"(plain |t|>1.96 would be cherry-picking).",
            "",
            "| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |",
            "|---|---|---|---|---|---|---|",
            *rows,
            "",
            "![chart](analysis_imbalance.png)",
            "",
            "**Read honestly:** a significant train t-stat with near-zero OOS "
            "correlation means the relationship did not survive the regime "
            "change between the two parts of the night. Only combos clearing "
            "the Bonferroni bar *and* showing same-signed OOS correlation "
            "deserve attention, and even those are one-night, one-venue results.",
        ]
    )
    save_outputs("analysis_imbalance", fig, md)


if __name__ == "__main__":
    main()
