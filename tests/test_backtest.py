"""Phase 4 tests: fills, fees, anti-lookahead, deflated Sharpe."""

import numpy as np
import pytest

from microstructure.backtest import (
    BookEvent,
    deflated_sharpe,
    random_strategy,
    run_backtest,
    walk_book,
)


def ev(ts: float, bid: float, ask: float, bid_q: float = 1.0, ask_q: float = 1.0) -> BookEvent:
    return BookEvent(ts, ((bid, bid_q),), ((ask, ask_q),))


def test_walk_book_vwap_across_levels() -> None:
    filled, vwap = walk_book(((100.2, 0.5), (100.3, 1.0)), 1.0)
    assert filled == pytest.approx(1.0)
    assert vwap == pytest.approx((0.5 * 100.2 + 0.5 * 100.3) / 1.0)


def test_walk_book_caps_at_displayed() -> None:
    filled, vwap = walk_book(((100.2, 0.5), (100.3, 1.0)), 5.0)
    assert filled == pytest.approx(1.5)  # remainder dropped, not queued
    assert vwap == pytest.approx((0.5 * 100.2 + 1.0 * 100.3) / 1.5)


def test_engine_fees_and_equity_hand_computed() -> None:
    events = [
        BookEvent(0.0, ((100.0, 1.0),), ((100.2, 0.5), (100.3, 1.0))),
        BookEvent(1.0, ((100.0, 1.0),), ((100.2, 0.5), (100.3, 1.0))),
    ]

    def strat(e: BookEvent, pos: float) -> float:
        return 1.0  # want 1 unit immediately

    res = run_backtest(iter(events), strat, initial_cash=10_000.0, fee=0.001)
    # decision at ev0 fills at ev1: 0.5@100.2 + 0.5@100.3, fee 10 bps
    notional = 0.5 * 100.2 + 0.5 * 100.3
    cash = 10_000.0 - notional - notional * 0.001
    assert res.n_trades == 1
    assert res.fees_paid == pytest.approx(notional * 0.001)
    assert res.equity.iloc[-1] == pytest.approx(cash + 1.0 * 100.1)


def test_engine_is_not_lookahead() -> None:
    # ask jumps from 100.2 to 105 after the decision: must pay 105
    events = [ev(0.0, 100.0, 100.2), ev(1.0, 100.0, 105.0)]

    def strat(e: BookEvent, pos: float) -> float:
        return 1.0 if e.ts == 0.0 else pos

    res = run_backtest(iter(events), strat, initial_cash=10_000.0, fee=0.0)
    assert res.equity.iloc[-1] == pytest.approx(10_000.0 - 105.0 + (100.0 + 105.0) / 2)


def test_buying_costs_the_spread() -> None:
    # buy then immediately sell on a static book: lose spread + fees
    events = [ev(float(t), 100.0, 100.2) for t in range(4)]

    def strat(e: BookEvent, pos: float) -> float:
        return 1.0 if e.ts < 2.0 else 0.0

    res = run_backtest(iter(events), strat, initial_cash=10_000.0, fee=0.001)
    expected_loss = 0.2 + 100.2 * 0.001 + 100.0 * 0.001  # spread + both fees
    assert res.equity.iloc[-1] == pytest.approx(10_000.0 - expected_loss)
    assert res.n_trades == 2


def test_random_strategy_deterministic_per_seed() -> None:
    events = [ev(float(t), 100.0, 100.2) for t in range(300)]
    r1 = run_backtest(iter(events), random_strategy(seed=7), fee=0.001)
    r2 = run_backtest(iter(events), random_strategy(seed=7), fee=0.001)
    assert r1.equity.equals(r2.equity)


def test_deflated_sharpe_behaves() -> None:
    # a solid Sharpe tested once survives
    assert deflated_sharpe(0.1, 5000, 0.0, 3.0, n_trials=1, var_trial_sr=0.0) > 0.99
    # a tiny Sharpe that is the best of 100 trials does not
    assert deflated_sharpe(0.01, 5000, 0.0, 3.0, n_trials=100, var_trial_sr=0.0004) < 0.5
    assert np.isnan(deflated_sharpe(0.1, 1, 0.0, 3.0, 1, 0.0))
