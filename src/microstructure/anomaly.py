"""Anomaly detection over the book stream.

All detectors compare a series against its own *trailing* robust
baseline (rolling median + MAD), so a detection at time t uses only
data ≤ t. Consecutive flagged seconds are collapsed into episodes.

Detectors:

* **spread spikes** — quoted spread far above its trailing median.
* **depth evaporation** — near-touch depth collapsing to a small
  fraction of its trailing median (quotes pulled).
* **vol regime shifts** — 1-min realized variance far above trailing.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import features as F

MAD_K = 1.4826  # MAD -> sigma under normality


@dataclass(frozen=True, slots=True)
class Episode:
    kind: str
    start: pd.Timestamp
    end: pd.Timestamp
    peak: float  # most extreme value during the episode
    baseline: float  # trailing median when the episode began

    @property
    def duration_s(self) -> float:
        return float((self.end - self.start).total_seconds())


def _episodes(flags: pd.Series, values: pd.Series, baseline: pd.Series, kind: str) -> list[Episode]:
    """Collapse a boolean flag series into contiguous episodes."""
    out: list[Episode] = []
    flagged = flags[flags].index
    if len(flagged) == 0:
        return out
    # split where the gap between consecutive flagged stamps exceeds 5 s
    breaks = np.where(np.diff(flagged.view(np.int64)) > 5e9)[0]
    starts = [0, *list(breaks + 1)]
    ends = [*list(breaks), len(flagged) - 1]
    for s_i, e_i in zip(starts, ends, strict=True):
        seg = values.loc[flagged[s_i] : flagged[e_i]]
        out.append(
            Episode(
                kind=kind,
                start=flagged[s_i],
                end=flagged[e_i],
                peak=float(seg.max()),
                baseline=float(baseline.loc[flagged[s_i]]),
            )
        )
    return out


def _trailing(
    series: pd.Series, window: str, min_periods: int = 30
) -> tuple[pd.Series, pd.Series]:
    """Trailing rolling median and MAD.

    The MAD is computed on deviations from the rolling median, which are
    only defined after the median's own warmup — so the MAD warms up in
    ``min_periods`` *additional* observations.
    """
    r = series.rolling(window, min_periods=min_periods)
    med = r.median()
    mad = (series - med).abs().rolling(window, min_periods=min_periods).median() * MAD_K
    return med, mad


def spread_spikes(
    book: pd.DataFrame, window: str = "15min", mult: float = 4.0, min_s: float = 3.0
) -> list[Episode]:
    """Quoted spread above ``mult``x its trailing median for >= ``min_s``.

    A multiplicative threshold, not a MAD one: tick-quantized spreads sit
    on a few discrete values, making the MAD tiny and z-scores explosive
    on routine one-tick flickers.
    """
    s = F.spread_bps(book).resample("1s").last().dropna()
    med, _ = _trailing(s, window)
    flags = s > mult * med
    eps = _episodes(flags.fillna(False), s, med, "spread_spike")
    return [e for e in eps if e.duration_s >= min_s]


def depth_evaporation(
    book: pd.DataFrame,
    window: str = "15min",
    frac: float = 0.15,
    bps: float = 10.0,
    min_s: float = 3.0,
) -> list[Episode]:
    """Near-touch depth below ``frac`` of its trailing median.

    Peak is reported as the *minimum* depth seen (inverted for the
    Episode.peak field convention: most extreme = smallest here).
    """
    d = (
        (F.depth_notional(book, "bid", bps) + F.depth_notional(book, "ask", bps))
        .resample("1s")
        .last()
        .dropna()
    )
    med, _ = _trailing(d, window)
    flags = d < frac * med
    eps = _episodes(flags.fillna(False), -d, med, "depth_evaporation")
    return [
        Episode(e.kind, e.start, e.end, peak=-e.peak, baseline=e.baseline)
        for e in eps
        if e.duration_s >= min_s
    ]


def vol_shifts(
    book: pd.DataFrame, window: str = "30min", n_sigmas: float = 6.0
) -> list[Episode]:
    """1-min realized variance above trailing median by ``n_sigmas`` MADs."""
    rv = F.realized_variance(F.mid(book), "1min").dropna()
    # 1-min bars accrue slowly; 30+30 bars of double warmup would eat an
    # hour, so use a shorter min_periods than the 1 s detectors
    med, mad = _trailing(rv, window, min_periods=15)
    flags = rv > med + n_sigmas * mad.replace(0.0, np.nan)
    return _episodes(flags.fillna(False), rv, med, "vol_shift")


def detect_all(book: pd.DataFrame) -> list[Episode]:
    """Run every detector, episodes sorted by start time."""
    eps = spread_spikes(book) + depth_evaporation(book) + vol_shifts(book)
    return sorted(eps, key=lambda e: e.start)
