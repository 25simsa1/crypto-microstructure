"""Runs test sanity checks (function lives in the tape analysis script)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from analysis_tape import runs_test_z


def test_runs_test_alternating_is_positive() -> None:
    s = pd.Series([1, -1] * 50)
    assert runs_test_z(s) > 5.0  # maximal alternation = far more runs than chance


def test_runs_test_persistent_is_negative() -> None:
    s = pd.Series([1] * 50 + [-1] * 50)
    assert runs_test_z(s) < -5.0  # two runs total = extreme persistence


def test_runs_test_random_is_small() -> None:
    rng = np.random.default_rng(3)
    s = pd.Series(rng.choice([1, -1], size=2000))
    assert abs(runs_test_z(s)) < 3.0


def test_runs_test_degenerate_is_nan() -> None:
    assert np.isnan(runs_test_z(pd.Series([1, 1, 1])))
