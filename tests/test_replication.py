"""Frozen-procedure sanity tests for the replication runner."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from replication_run import epps_curve, tick_sign_stats


def _mid(vals: list[float], freq: str = "1s") -> pd.Series:
    idx = pd.date_range("2026-06-11 08:03:00", periods=len(vals), freq=freq, tz="UTC")
    return pd.Series(vals, index=idx)


def test_tick_sign_stats_alternating_is_negative() -> None:
    # mid strictly alternates up/down -> tick signs alternate -> ACF(1) = -1
    vals = [100.0 + (0.1 if i % 2 else 0.0) for i in range(200)]
    acf, lb, n = tick_sign_stats(_mid(vals))
    assert n == 199
    assert acf < -0.1
    assert lb < 1e-10


def test_tick_sign_stats_too_few_ticks_is_nan() -> None:
    acf, _lb, n = tick_sign_stats(_mid([100.0] * 100))  # zero changes
    assert n == 0
    assert np.isnan(acf)


def test_epps_curve_perfectly_synchronous_is_flat_high() -> None:
    rng = np.random.default_rng(0)
    walk = 100 * np.exp(np.cumsum(rng.normal(0, 1e-4, 4000)))
    a, b = _mid(list(walk)), _mid(list(walk * 1.5))  # identical returns
    curve = epps_curve(a, b)
    assert all(c == pytest.approx(1.0) for c in curve)
