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


def depth_profile(
    book: pd.DataFrame, bands_bps: tuple[float, ...] = (1, 5, 10, 25, 50)
) -> pd.DataFrame:
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


# ---------------------------------------------------------------------------
# trade-tape features (need the trades frame from parquet.load_trades)
# ---------------------------------------------------------------------------


def effective_spread_bps(trades: pd.DataFrame, mid_series: pd.Series) -> pd.Series:
    """Effective spread per trade: ``2 * |p - m| / m * 1e4`` bps.

    ``m`` is the prevailing mid — the last book mid at or before the
    trade (asof join; trades before the first snapshot are dropped).
    Compare to the *quoted* spread: effective < quoted means trades
    happen inside the touch; effective > quoted means takers ate
    through the level or the 1 s mid is stale.
    """
    mid_sorted = mid_series.sort_index()
    m = pd.merge_asof(
        trades[["price"]].sort_index(),
        mid_sorted.rename("mid"),
        left_index=True,
        right_index=True,
        direction="backward",
    ).dropna()
    return (2.0 * (m["price"] - m["mid"]).abs() / m["mid"] * 1e4).rename("eff_spread_bps")


def trade_sign_autocorr(trades: pd.DataFrame, max_lag: int = 50) -> pd.Series:
    """Autocorrelation of trade signs at lags 1..``max_lag`` (in trades).

    Order flow has long memory (Lillo & Farmer 2004): signs decay
    slowly because large parent orders are sliced. Index = lag.
    """
    signs = np.sign(trades["signed_qty"]).astype(float)
    acf = {k: float(signs.autocorr(lag=k)) for k in range(1, max_lag + 1)}
    return pd.Series(acf, name="sign_acf")


def volume_bars(trades: pd.DataFrame, bucket_qty: float) -> pd.DataFrame:
    """Aggregate trades into equal-*volume* bars of ``bucket_qty`` base units.

    Each bar reports open/high/low/close/vwap, total qty, net signed
    qty, and the wall-clock seconds it took to fill — the 'volume
    clock' (Easley, López de Prado & O'Hara): bars fill fast when
    activity is high, so bar returns are closer to homoskedastic than
    time bars. The trailing partial bucket is dropped.
    """
    cum = trades["qty"].cumsum()
    # assign by cumulative volume *before* the trade so the fill that
    # completes a bucket belongs to that bucket, not the next one; the
    # epsilon keeps float cumsum error (2.0 -> 1.999...8) from shifting
    # boundary trades into the wrong bucket
    bar_id = np.floor((cum - trades["qty"]) / bucket_qty + 1e-9).astype(int)
    g = trades.groupby(bar_id)
    out = pd.DataFrame(
        {
            "open": g["price"].first(),
            "high": g["price"].max(),
            "low": g["price"].min(),
            "close": g["price"].last(),
            "vwap": g.apply(lambda x: float((x["price"] * x["qty"]).sum() / x["qty"].sum())),
            "qty": g["qty"].sum(),
            "net_signed_qty": g["signed_qty"].sum(),
            "start": g.apply(lambda x: x.index[0]),
            "seconds": g.apply(lambda x: (x.index[-1] - x.index[0]).total_seconds()),
        }
    )
    if len(out) > 0 and out["qty"].iloc[-1] < bucket_qty * 0.999:
        out = out.iloc[:-1]  # trailing partial bucket
    return out
