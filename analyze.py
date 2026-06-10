#!/usr/bin/env python3
"""Morning analysis of overnight order-book snapshots.

Reads every data/book-*.jsonl.gz, then per symbol reports:
  - spread (absolute and basis points): mean / median / p95
  - depth within 0.1% and 0.5% of mid (quote-currency notional)
  - realized volatility of the mid price (1-min returns, annualized)
  - bid/ask depth imbalance
and saves an overview chart to report.png.

Run:  python3 analyze.py
"""

import glob
import gzip
import json
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_DIR = Path(__file__).parent / "data"


def load_snapshots():
    rows = []
    files = sorted(glob.glob(str(DATA_DIR / "book-*.jsonl.gz")))
    if not files:
        raise SystemExit("no data files found in data/ — did the logger run?")
    for f in files:
        with gzip.open(f, "rt") as fh:
            while True:
                try:
                    line = fh.readline()
                except EOFError:
                    break  # file still being written; tail not flushed yet
                if not line:
                    break
                try:
                    snap = json.loads(line)
                except json.JSONDecodeError:
                    continue  # torn final line from a crash
                bids = [(float(p), float(q)) for p, q in snap["bids"]]
                asks = [(float(p), float(q)) for p, q in snap["asks"]]
                if not bids or not asks:
                    continue
                bb, ba = bids[0][0], asks[0][0]
                mid = (bb + ba) / 2
                rows.append(
                    {
                        "ts": snap["ts"],
                        "symbol": snap["symbol"],
                        "mid": mid,
                        "spread": ba - bb,
                        "spread_bps": (ba - bb) / mid * 1e4,
                        "bid_depth_10bps": sum(
                            p * q for p, q in bids if p >= mid * 0.999
                        ),
                        "ask_depth_10bps": sum(
                            p * q for p, q in asks if p <= mid * 1.001
                        ),
                        "bid_depth_50bps": sum(
                            p * q for p, q in bids if p >= mid * 0.995
                        ),
                        "ask_depth_50bps": sum(
                            p * q for p, q in asks if p <= mid * 1.005
                        ),
                    }
                )
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["ts"], unit="s", utc=True).dt.tz_convert(
        "America/Los_Angeles"
    )
    return df.set_index("time").sort_index()


def report(df: pd.DataFrame):
    print(f"{len(df):,} snapshots, {df.index.min()} -> {df.index.max()}\n")
    for sym, g in df.groupby("symbol"):
        mid_1m = g["mid"].resample("1min").last().dropna()
        rets = mid_1m.pct_change().dropna()
        # annualize 1-min returns: sqrt(minutes per year)
        ann_vol = rets.std() * (365 * 24 * 60) ** 0.5 * 100
        imb = (g["bid_depth_10bps"] - g["ask_depth_10bps"]) / (
            g["bid_depth_10bps"] + g["ask_depth_10bps"]
        )
        print(f"=== {sym.upper()} ===")
        print(f"  snapshots:          {len(g):,}")
        print(f"  mid price range:    {g['mid'].min():,.2f} - {g['mid'].max():,.2f}")
        print(
            f"  spread:             mean {g['spread_bps'].mean():.2f} bps | "
            f"median {g['spread_bps'].median():.2f} | p95 {g['spread_bps'].quantile(0.95):.2f}"
        )
        print(
            f"  depth ±0.1% of mid: bid ${g['bid_depth_10bps'].mean():,.0f} | "
            f"ask ${g['ask_depth_10bps'].mean():,.0f}"
        )
        print(
            f"  depth ±0.5% of mid: bid ${g['bid_depth_50bps'].mean():,.0f} | "
            f"ask ${g['ask_depth_50bps'].mean():,.0f}"
        )
        print(f"  book imbalance:     mean {imb.mean():+.3f} (+ = bid-heavy)")
        print(f"  realized vol (1m):  {ann_vol:.1f}% annualized\n")


def chart(df: pd.DataFrame):
    symbols = sorted(df["symbol"].unique())
    fig, axes = plt.subplots(
        3, len(symbols), figsize=(6 * len(symbols), 10), sharex=True
    )
    if len(symbols) == 1:
        axes = axes.reshape(3, 1)
    for i, sym in enumerate(symbols):
        g = df[df["symbol"] == sym].resample("1min").mean(numeric_only=True)
        axes[0][i].plot(g.index, g["mid"])
        axes[0][i].set_title(f"{sym.upper()} mid price")
        axes[1][i].plot(g.index, g["spread_bps"], color="tab:orange")
        axes[1][i].set_title("spread (bps, 1-min mean)")
        axes[2][i].plot(g.index, g["bid_depth_10bps"], label="bid", alpha=0.8)
        axes[2][i].plot(g.index, g["ask_depth_10bps"], label="ask", alpha=0.8)
        axes[2][i].set_title("depth within ±0.1% of mid ($)")
        axes[2][i].legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    out = Path(__file__).parent / "report.png"
    fig.savefig(out, dpi=120)
    print(f"chart saved to {out}")


if __name__ == "__main__":
    df = load_snapshots()
    report(df)
    chart(df)
