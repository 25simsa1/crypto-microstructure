"""Shared helpers for the analysis scripts in ``scripts/``."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .parquet import build_book_parquet, build_trade_parquet, load_books

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
PARQUET_DIR = ROOT / "parquet"
OUTPUT_DIR = ROOT / "output"

SYMBOLS = ("btcusdt", "ethusdt", "solusdt")

plt.rcParams.update(
    {
        "figure.dpi": 120,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 9,
    }
)


def refresh_parquet() -> None:
    """Bring the Parquet store up to date with the live capture."""
    build_book_parquet(DATA_DIR, PARQUET_DIR)
    build_trade_parquet(DATA_DIR, PARQUET_DIR)


def load_all_books() -> dict[str, pd.DataFrame]:
    """Load the full flattened book history for every symbol."""
    return {s: load_books(PARQUET_DIR, s) for s in SYMBOLS}


def aligned_mids(books: dict[str, pd.DataFrame], freq: str = "1s") -> pd.DataFrame:
    """Last-observation mid per symbol on a common regular grid.

    Resamples with *last* (no interpolation across gaps — interpolating
    would smear information backwards in time).
    """
    cols = {}
    for sym, book in books.items():
        m = (book["bid_px_0"] + book["ask_px_0"]) / 2.0
        cols[sym] = m.resample(freq).last()
    return pd.DataFrame(cols).dropna(how="all")


def save_outputs(name: str, fig: plt.Figure, markdown: str) -> tuple[Path, Path]:
    """Write ``output/<name>.png`` and ``output/<name>.md``."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    png = OUTPUT_DIR / f"{name}.png"
    md = OUTPUT_DIR / f"{name}.md"
    fig.savefig(png, bbox_inches="tight")
    plt.close(fig)
    md.write_text(markdown)
    print(f"wrote {png.name} + {md.name}")
    return png, md


def data_span_note(books: dict[str, pd.DataFrame]) -> str:
    """One-line caveat about how much data the figures rest on."""
    starts = [b.index.min() for b in books.values()]
    ends = [b.index.max() for b in books.values()]
    span_h = (max(ends) - min(starts)).total_seconds() / 3600
    return (
        f"_Data: {min(starts):%Y-%m-%d %H:%M} → {max(ends):%H:%M} UTC "
        f"(~{span_h:.1f} h of single-venue Binance.US capture). "
        "Conclusions are conditional on this one overnight session._"
    )
