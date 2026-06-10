"""Microstructure feature library.

All functions operate on the flattened book DataFrames produced by
:mod:`microstructure.parquet` (columns ``bid_px_i``, ``bid_qty_i``,
``ask_px_i``, ``ask_qty_i`` for ``i`` in ``0..19``, indexed by UTC
timestamp) and return Series/DataFrames aligned to the input index.

Definitions follow the standard literature; each docstring states the
exact formula so results can be checked by hand.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# prices and spreads
# ---------------------------------------------------------------------------


def mid(book: pd.DataFrame) -> pd.Series:
    """Arithmetic mid: ``(best_bid + best_ask) / 2``."""
    return (book["bid_px_0"] + book["ask_px_0"]) / 2.0


def weighted_mid(book: pd.DataFrame) -> pd.Series:
    """Size-weighted average of the touch prices.

    ``(Pb*Qb + Pa*Qa) / (Qb + Qa)`` — leans toward the *larger* side.
    """
    qb, qa = book["bid_qty_0"], book["ask_qty_0"]
    return (book["bid_px_0"] * qb + book["ask_px_0"] * qa) / (qb + qa)


def microprice(book: pd.DataFrame) -> pd.Series:
    """Stoikov microprice: ``(Qb*Pa + Qa*Pb) / (Qb + Qa)``.

    The expected next mid: a large *bid* queue pushes the fair price
    toward the *ask* (buy pressure), and vice versa.
    """
    qb, qa = book["bid_qty_0"], book["ask_qty_0"]
    return (qb * book["ask_px_0"] + qa * book["bid_px_0"]) / (qb + qa)


def spread_bps(book: pd.DataFrame) -> pd.Series:
    """Quoted spread in basis points of the mid: ``(Pa - Pb) / mid * 1e4``."""
    return (book["ask_px_0"] - book["bid_px_0"]) / mid(book) * 1e4


# ---------------------------------------------------------------------------
# depth and imbalance
# ---------------------------------------------------------------------------


def _side_qty(book: pd.DataFrame, side: str, levels: int) -> pd.Series:
    cols = [f"{side}_qty_{i}" for i in range(levels)]
    return book[cols].fillna(0.0).sum(axis=1)


def imbalance(book: pd.DataFrame, levels: int = 1) -> pd.Series:
    """Order book imbalance over the top ``levels``:

    ``(sum Qb - sum Qa) / (sum Qb + sum Qa)`` in ``[-1, 1]``; positive
    means a bid-heavy (buy-pressured) book.
    """
    qb = _side_qty(book, "bid", levels)
    qa = _side_qty(book, "ask", levels)
    return (qb - qa) / (qb + qa)


def depth_notional(book: pd.DataFrame, side: str, within_bps: float) -> pd.Series:
    """Quote-currency notional resting within ``within_bps`` of the mid.

    Sums ``price * qty`` over recorded levels whose price is within the
    band; deeper liquidity outside the recorded 20 levels is invisible.
    """
    m = mid(book)
    band = within_bps / 1e4
    total = pd.Series(0.0, index=book.index)
    for i in range(20):
        px, qty = book[f"{side}_px_{i}"], book[f"{side}_qty_{i}"]
        in_band = (px >= m * (1 - band)) if side == "bid" else (px <= m * (1 + band))
        total = total + (px * qty).where(in_band & px.notna(), 0.0)
    return total


def depth_profile(book: pd.DataFrame, bands_bps: tuple[float, ...] = (1, 5, 10, 25, 50)) -> pd.DataFrame:
    """Bid/ask notional within each band of the mid, one column per band."""
    out = {}
    for b in bands_bps:
        out[f"bid_{b:g}bps"] = depth_notional(book, "bid", b)
        out[f"ask_{b:g}bps"] = depth_notional(book, "ask", b)
    return pd.DataFrame(out, index=book.index)


# ---------------------------------------------------------------------------
# order flow imbalance (Cont, Kukanov & Stoikov 2014)
# ---------------------------------------------------------------------------


def ofi(book: pd.DataFrame) -> pd.Series:
    """Best-level order flow imbalance between consecutive snapshots.

    ``e_n = qb_n*1{Pb_n>=Pb_{n-1}} - qb_{n-1}*1{Pb_n<=Pb_{n-1}}
           - qa_n*1{Pa_n<=Pa_{n-1}} + qa_{n-1}*1{Pa_n>=Pa_{n-1}}``

    Positive OFI = net addition of buy interest / removal of sell
    interest. With 1 s snapshots this is a *sampled* OFI, coarser than
    the per-event version in the paper.
    """
    pb, qb = book["bid_px_0"], book["bid_qty_0"]
    pa, qa = book["ask_px_0"], book["ask_qty_0"]
    pb1, qb1, pa1, qa1 = pb.shift(), qb.shift(), pa.shift(), qa.shift()
    e = (
        qb.where(pb >= pb1, 0.0)
        - qb1.where(pb <= pb1, 0.0)
        - qa.where(pa <= pa1, 0.0)
        + qa1.where(pa >= pa1, 0.0)
    )
    e.iloc[0] = np.nan  # no predecessor
    return e


# ---------------------------------------------------------------------------
# realized volatility estimators
# ---------------------------------------------------------------------------


def realized_variance(prices: pd.Series, bar: str = "1min") -> pd.Series:
    """Per-bar realized variance: sum of squared log returns within the bar.

    Input is the (irregular) mid series; returns are computed tick-to-tick
    then aggregated, so bars with no data are NaN.
    """
    r2 = np.log(prices).diff() ** 2
    return r2.resample(bar).sum(min_count=1)


def parkinson_variance(prices: pd.Series, bar: str = "1min") -> pd.Series:
    """Parkinson (1980) high-low variance per bar:

    ``(ln(H/L))^2 / (4 ln 2)`` — efficient for ranges, assumes no drift
    within the bar.
    """
    hi = prices.resample(bar).max()
    lo = prices.resample(bar).min()
    return np.log(hi / lo) ** 2 / (4.0 * np.log(2.0))


def bipower_variation(prices: pd.Series, bar: str = "1min") -> pd.Series:
    """Bipower variation per bar (Barndorff-Nielsen & Shephard 2004):

    ``(pi/2) * sum |r_i| |r_{i-1}|`` — a jump-robust variance estimate;
    realized variance minus bipower estimates the jump component.
    """
    r = np.log(prices).diff().abs()
    cross = r * r.shift()
    return (np.pi / 2.0) * cross.resample(bar).sum(min_count=1)


def annualize_variance(var_per_bar: pd.Series, bar_seconds: float) -> pd.Series:
    """Convert per-bar variance to annualized volatility (24/7 market)."""
    bars_per_year = 365.0 * 24 * 3600 / bar_seconds
    return np.sqrt(var_per_bar * bars_per_year)


# ---------------------------------------------------------------------------
# rolling wrappers
# ---------------------------------------------------------------------------


def rolling_mean(s: pd.Series, window: str = "5min", min_periods: int = 10) -> pd.Series:
    """Time-based rolling mean (window like ``'5min'``)."""
    return s.rolling(window, min_periods=min_periods).mean()


def rolling_zscore(s: pd.Series, window: str = "30min", min_periods: int = 30) -> pd.Series:
    """Rolling z-score: ``(x - rolling mean) / rolling std``.

    Uses only past data within the window — safe for predictive studies.
    """
    r = s.rolling(window, min_periods=min_periods)
    return (s - r.mean()) / r.std()
