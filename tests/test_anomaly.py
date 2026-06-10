"""Anomaly detector tests on synthetic books with planted events."""

import numpy as np
import pandas as pd

from microstructure.anomaly import depth_evaporation, spread_spikes, vol_shifts


def synth_book(
    n: int = 1800,
    spread: float = 0.02,
    qty: float = 5.0,
    spike_at: slice | None = None,
    spike_spread: float = 0.5,
    drain_at: slice | None = None,
) -> pd.DataFrame:
    """Flat 100.00/100.02 book; optionally widen the spread or drain qty."""
    idx = pd.date_range("2026-06-10 05:00:00", periods=n, freq="1s", tz="UTC")
    spreads = np.full(n, spread)
    if spike_at is not None:
        spreads[spike_at] = spike_spread
    qtys = np.full(n, qty)
    if drain_at is not None:
        qtys[drain_at] = qty * 0.01
    df = pd.DataFrame(index=idx)
    df["bid_px_0"] = 100.0
    df["ask_px_0"] = 100.0 + spreads
    df["bid_qty_0"] = qtys
    df["ask_qty_0"] = qtys
    for i in range(1, 20):
        df[f"bid_px_{i}"] = np.nan
        df[f"ask_px_{i}"] = np.nan
        df[f"bid_qty_{i}"] = 0.0
        df[f"ask_qty_{i}"] = 0.0
    # tiny noise so MAD is nonzero (a perfectly constant series has MAD 0)
    rng = np.random.default_rng(0)
    df["ask_px_0"] += rng.normal(0, 0.0005, n).round(4)
    return df


def test_spread_spike_detected_and_quiet_book_clean() -> None:
    quiet = synth_book()
    assert spread_spikes(quiet) == []
    spiky = synth_book(spike_at=slice(1200, 1230))
    eps = spread_spikes(spiky)
    assert len(eps) == 1
    assert eps[0].kind == "spread_spike"
    assert eps[0].start == spiky.index[1200]
    assert eps[0].duration_s <= 35
    assert eps[0].peak > 40.0  # ~0.5 on 100 = 50 bps


def test_depth_evaporation_detected() -> None:
    drained = synth_book(drain_at=slice(1400, 1410))
    eps = depth_evaporation(drained)
    assert len(eps) == 1
    e = eps[0]
    assert e.kind == "depth_evaporation"
    assert e.start == drained.index[1400]
    assert e.peak < 0.05 * e.baseline  # depth fell to ~1% of baseline


def test_vol_shift_detected() -> None:
    book = synth_book(n=3600)
    # plant a 5-minute burst of large mid moves late in the series
    burst = slice(3000, 3300)
    walk = np.cumsum(np.random.default_rng(1).normal(0, 0.05, 300))
    book.loc[book.index[burst], "bid_px_0"] += walk
    book.loc[book.index[burst], "ask_px_0"] += walk
    eps = vol_shifts(book)
    assert len(eps) >= 1
    assert all(e.kind == "vol_shift" for e in eps)
    assert eps[0].start >= book.index[2940]  # within/after the burst's first bar
