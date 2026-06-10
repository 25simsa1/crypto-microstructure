"""Phase 2 tests: every feature checked against hand-computed numbers."""

import numpy as np
import pandas as pd
import pytest

from microstructure import features as F


def make_book(rows: list[dict]) -> pd.DataFrame:
    """Build a full 20-level book frame; unspecified levels are NaN px / 0 qty."""
    full = []
    for r in rows:
        row = {}
        for i in range(20):
            for side in ("bid", "ask"):
                row[f"{side}_px_{i}"] = r.get(f"{side}_px_{i}", np.nan)
                row[f"{side}_qty_{i}"] = r.get(f"{side}_qty_{i}", 0.0)
        full.append(row)
    idx = pd.date_range("2026-06-10 05:00:00", periods=len(rows), freq="1s", tz="UTC")
    return pd.DataFrame(full, index=idx)


ROW = {
    "bid_px_0": 100.0, "bid_qty_0": 2.0, "ask_px_0": 100.2, "ask_qty_0": 1.0,
    "bid_px_1": 99.9, "bid_qty_1": 3.0, "ask_px_1": 100.3, "ask_qty_1": 4.0,
}


def test_mid_weighted_mid_microprice_spread() -> None:
    book = make_book([ROW])
    assert F.mid(book).iloc[0] == pytest.approx(100.1)
    # weighted mid: (100*2 + 100.2*1) / 3
    assert F.weighted_mid(book).iloc[0] == pytest.approx(300.2 / 3)
    # microprice: (2*100.2 + 1*100) / 3 — big bid queue pulls price toward ask
    assert F.microprice(book).iloc[0] == pytest.approx(300.4 / 3)
    assert F.microprice(book).iloc[0] > F.mid(book).iloc[0]
    # spread: 0.2 / 100.1 * 1e4
    assert F.spread_bps(book).iloc[0] == pytest.approx(0.2 / 100.1 * 1e4)


def test_imbalance_multiple_depths() -> None:
    book = make_book([ROW])
    # level 1: (2-1)/(2+1)
    assert F.imbalance(book, levels=1).iloc[0] == pytest.approx(1 / 3)
    # levels 1-2: bids 2+3, asks 1+4 → (5-5)/10
    assert F.imbalance(book, levels=2).iloc[0] == pytest.approx(0.0)


def test_depth_notional_band_cutoff() -> None:
    book = make_book([ROW])
    # mid 100.1, 10 bps band = ±0.1001 → only level 0 qualifies on each side
    assert F.depth_notional(book, "bid", 10).iloc[0] == pytest.approx(100.0 * 2.0)
    assert F.depth_notional(book, "ask", 10).iloc[0] == pytest.approx(100.2 * 1.0)
    # 50 bps band (±0.5005) reaches level 1 too
    assert F.depth_notional(book, "bid", 50).iloc[0] == pytest.approx(200.0 + 99.9 * 3.0)
    profile = F.depth_profile(book, bands_bps=(10, 50))
    assert profile["ask_50bps"].iloc[0] == pytest.approx(100.2 + 100.3 * 4.0)


def test_ofi_hand_computed() -> None:
    rows = [
        {"bid_px_0": 100.0, "bid_qty_0": 2.0, "ask_px_0": 100.2, "ask_qty_0": 1.0},
        # bid price up (new queue counts), ask price flat (both terms count)
        {"bid_px_0": 100.1, "bid_qty_0": 5.0, "ask_px_0": 100.2, "ask_qty_0": 4.0},
        # bid price down (old queue removed), ask price up (old ask queue freed)
        {"bid_px_0": 100.0, "bid_qty_0": 7.0, "ask_px_0": 100.3, "ask_qty_0": 2.0},
    ]
    e = F.ofi(make_book(rows))
    assert np.isnan(e.iloc[0])
    assert e.iloc[1] == pytest.approx(5.0 - 4.0 + 1.0)  # = 2
    assert e.iloc[2] == pytest.approx(-5.0 + 4.0)  # = -1


def _price_series(vals: list[float], step_s: int = 10) -> pd.Series:
    idx = pd.date_range("2026-06-10 05:00:00", periods=len(vals), freq=f"{step_s}s", tz="UTC")
    return pd.Series(vals, index=idx)


def test_realized_variance_hand_computed() -> None:
    rv = F.realized_variance(_price_series([100.0, 101.0]), bar="1min")
    assert rv.iloc[0] == pytest.approx(np.log(1.01) ** 2)


def test_parkinson_hand_computed() -> None:
    pv = F.parkinson_variance(_price_series([100.0, 101.0, 100.5]), bar="1min")
    assert pv.iloc[0] == pytest.approx(np.log(101.0 / 100.0) ** 2 / (4 * np.log(2)))


def test_bipower_hand_computed() -> None:
    bv = F.bipower_variation(_price_series([100.0, 101.0, 100.5]), bar="1min")
    r1, r2 = np.log(101 / 100), abs(np.log(100.5 / 101))
    assert bv.iloc[0] == pytest.approx(np.pi / 2 * r1 * r2)


def test_annualize_variance() -> None:
    # variance 1e-8 per 60s bar → vol = sqrt(1e-8 * 525600) annualized
    out = F.annualize_variance(pd.Series([1e-8]), bar_seconds=60)
    assert out.iloc[0] == pytest.approx(np.sqrt(1e-8 * 365 * 24 * 60))


def test_rolling_zscore_is_backward_looking() -> None:
    # step at the end: z-score must use only past data, so the spike is large
    s = _price_series([1.0] * 40 + [2.0], step_s=1)
    z = F.rolling_zscore(s, window="30s", min_periods=5)
    assert z.iloc[-1] > 3.0
    # constant history → std 0 → earlier values are nan or 0, never inf
    assert not np.isinf(z.fillna(0.0)).any()


# ---------------------------------------------------------------------------
# trade-tape features
# ---------------------------------------------------------------------------


def make_trades(prices: list[float], qtys: list[float], signs: list[int]) -> pd.DataFrame:
    idx = pd.date_range("2026-06-10 05:00:00", periods=len(prices), freq="1s", tz="UTC")
    return pd.DataFrame(
        {
            "price": prices,
            "qty": qtys,
            "signed_qty": [q * s for q, s in zip(qtys, signs, strict=True)],
        },
        index=idx,
    )


def test_effective_spread_hand_computed() -> None:
    mid_idx = pd.date_range("2026-06-10 04:59:59", periods=1, freq="1s", tz="UTC")
    mids = pd.Series([100.0], index=mid_idx)
    trades = make_trades([100.05], [1.0], [1])
    es = F.effective_spread_bps(trades, mids)
    # 2 * |100.05 - 100| / 100 * 1e4 = 10 bps
    assert es.iloc[0] == pytest.approx(10.0)


def test_effective_spread_drops_trades_before_first_mid() -> None:
    mid_idx = pd.date_range("2026-06-10 05:00:30", periods=1, freq="1s", tz="UTC")
    mids = pd.Series([100.0], index=mid_idx)
    trades = make_trades([100.05, 100.1], [1.0, 1.0], [1, 1])  # both before 05:00:30
    assert len(F.effective_spread_bps(trades, mids)) == 0


def test_trade_sign_autocorr_alternating() -> None:
    trades = make_trades([100.0] * 8, [1.0] * 8, [1, -1, 1, -1, 1, -1, 1, -1])
    acf = F.trade_sign_autocorr(trades, max_lag=2)
    assert acf.loc[1] == pytest.approx(-1.0)
    assert acf.loc[2] == pytest.approx(1.0)


def test_volume_bars_hand_computed() -> None:
    trades = make_trades(
        [100.0, 101.0, 102.0, 103.0, 104.0],
        [0.4, 0.6, 0.5, 0.5, 0.3],
        [1, -1, 1, 1, 1],
    )
    bars = F.volume_bars(trades, bucket_qty=1.0)
    assert len(bars) == 2  # trailing 0.3 partial dropped
    assert bars["qty"].iloc[0] == pytest.approx(1.0)
    assert bars["open"].iloc[0] == 100.0
    assert bars["close"].iloc[0] == 101.0
    assert bars["vwap"].iloc[0] == pytest.approx(100.0 * 0.4 + 101.0 * 0.6)
    assert bars["net_signed_qty"].iloc[0] == pytest.approx(0.4 - 0.6)
    assert bars["vwap"].iloc[1] == pytest.approx(102.5)
    assert bars["seconds"].iloc[0] == pytest.approx(1.0)
