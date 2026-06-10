"""Research-grade event-driven backtest over recorded book snapshots.

Execution model (deliberately pessimistic, taker-only):

* Orders are market orders triggered by a strategy's target position.
* Buys walk the recorded ask side level by level (sells walk bids),
  filling at displayed prices — you pay the spread, always.
* You cannot fill more than the displayed size across the recorded 20
  levels; any remainder is **dropped**, not queued.
* Taker fee applies to every fill (default 10 bps per side).
* Equity is marked to the arithmetic mid.

What this harness can NOT model (single venue, 1 s snapshots):

* Queue position / maker fills — no order book deltas between snapshots.
* Latency: fills happen at the *next* snapshot after a decision, ~1 s —
  far slower than real HFT, but honest for snapshot data.
* Market impact beyond the displayed book, and self-impact persistence.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

TAKER_FEE = 0.001  # 10 bps per side


# ---------------------------------------------------------------------------
# events and fills
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BookEvent:
    ts: float
    bids: tuple[tuple[float, float], ...]  # (price, displayed qty), best first
    asks: tuple[tuple[float, float], ...]

    @property
    def mid(self) -> float:
        return (self.bids[0][0] + self.asks[0][0]) / 2.0


def book_events(book: pd.DataFrame, n_levels: int = 20) -> Iterator[BookEvent]:
    """Convert a flattened book frame into replayable events."""
    cols = book[
        [f"{s}_{w}_{i}" for i in range(n_levels) for s in ("bid", "ask") for w in ("px", "qty")]
    ].to_numpy()
    ts_arr = book["ts"].to_numpy()
    for row_idx in range(len(book)):
        row = cols[row_idx]
        bids, asks = [], []
        for i in range(n_levels):
            bp, bq, ap, aq = row[4 * i : 4 * i + 4]
            if np.isfinite(bp) and bq > 0:
                bids.append((float(bp), float(bq)))
            if np.isfinite(ap) and aq > 0:
                asks.append((float(ap), float(aq)))
        if bids and asks:
            yield BookEvent(float(ts_arr[row_idx]), tuple(bids), tuple(asks))


def walk_book(
    levels: tuple[tuple[float, float], ...], qty: float
) -> tuple[float, float]:
    """Fill ``qty`` against displayed levels.

    Returns ``(filled_qty, vwap)``. Fills are capped at total displayed
    size; the unfilled remainder is dropped.
    """
    remaining = qty
    cost = 0.0
    for price, size in levels:
        take = min(remaining, size)
        cost += take * price
        remaining -= take
        if remaining <= 1e-12:
            break
    filled = qty - max(remaining, 0.0)
    return (filled, cost / filled) if filled > 0 else (0.0, float("nan"))


# ---------------------------------------------------------------------------
# strategies
# ---------------------------------------------------------------------------

# A strategy maps (event, current position in base units) -> target position.
Strategy = Callable[[BookEvent, float], float]


def random_strategy(seed: int, trade_every_s: float = 60.0, size: float = 0.001) -> Strategy:
    """Null baseline: coin-flip ±size position, reconsidered every minute.

    Any 'edge' this shows is what the harness + data hand to luck; real
    strategies must beat its distribution, not zero.
    """
    rng = np.random.default_rng(seed)
    state = {"next_ts": 0.0, "target": 0.0}

    def strat(ev: BookEvent, pos: float) -> float:
        if ev.ts >= state["next_ts"]:
            state["target"] = size if rng.random() < 0.5 else -size
            state["next_ts"] = ev.ts + trade_every_s
        return state["target"]

    return strat


def imbalance_strategy(
    levels: int = 5, threshold: float = 0.6, size: float = 0.001, hold_s: float = 30.0
) -> Strategy:
    """Long when the top-``levels`` book is bid-heavy beyond ``threshold``,
    short when ask-heavy, flat otherwise; positions held >= ``hold_s``."""
    state = {"until": 0.0}

    def strat(ev: BookEvent, pos: float) -> float:
        if ev.ts < state["until"]:
            return pos
        qb = sum(q for _, q in ev.bids[:levels])
        qa = sum(q for _, q in ev.asks[:levels])
        imb = (qb - qa) / (qb + qa)
        if imb > threshold:
            state["until"] = ev.ts + hold_s
            return size
        if imb < -threshold:
            state["until"] = ev.ts + hold_s
            return -size
        return 0.0

    return strat


# ---------------------------------------------------------------------------
# engine
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class BacktestResult:
    equity: pd.Series  # marked-to-mid, indexed by ts
    n_trades: int
    fees_paid: float
    volume: float  # quote-currency notional traded

    @property
    def returns(self) -> pd.Series:
        return self.equity.pct_change().dropna()

    def sharpe(self, bar_seconds: float = 1.0) -> float:
        r = self.returns
        if len(r) < 2 or r.std() == 0:
            return 0.0
        ann = np.sqrt(365 * 24 * 3600 / bar_seconds)
        return float(r.mean() / r.std() * ann)

    @property
    def max_drawdown(self) -> float:
        eq = self.equity
        return float((eq / eq.cummax() - 1.0).min())


def run_backtest(
    events: Iterator[BookEvent],
    strategy: Strategy,
    initial_cash: float = 10_000.0,
    fee: float = TAKER_FEE,
) -> BacktestResult:
    """Replay events; decisions at event t execute against event t+1's book.

    The one-event execution delay is the anti-lookahead guarantee: a
    strategy can never trade at prices it used to decide.
    """
    cash, pos = initial_cash, 0.0
    pending: float | None = None
    n_trades, fees_paid, volume = 0, 0.0, 0.0
    eq_ts: list[float] = []
    eq_val: list[float] = []

    for ev in events:
        if pending is not None:
            delta = pending - pos
            if abs(delta) > 1e-12:
                side = ev.asks if delta > 0 else ev.bids
                filled, vwap = walk_book(side, abs(delta))
                if filled > 0:
                    notional = filled * vwap
                    fee_cost = notional * fee
                    cash += -notional - fee_cost if delta > 0 else notional - fee_cost
                    pos += filled if delta > 0 else -filled
                    n_trades += 1
                    fees_paid += fee_cost
                    volume += notional
            pending = None
        target = strategy(ev, pos)
        if abs(target - pos) > 1e-12:
            pending = target
        eq_ts.append(ev.ts)
        eq_val.append(cash + pos * ev.mid)

    idx = pd.to_datetime(pd.Index(eq_ts), unit="s", utc=True)
    return BacktestResult(
        equity=pd.Series(eq_val, index=idx),
        n_trades=n_trades,
        fees_paid=fees_paid,
        volume=volume,
    )


# ---------------------------------------------------------------------------
# multiple-testing-aware Sharpe evaluation
# ---------------------------------------------------------------------------


def deflated_sharpe(
    sr: float,
    n_obs: int,
    skew: float,
    kurt: float,
    n_trials: int,
    var_trial_sr: float,
) -> float:
    """Deflated Sharpe Ratio (Bailey & López de Prado 2014).

    Probability that the observed (non-annualized, per-bar) Sharpe ``sr``
    exceeds the expected maximum Sharpe of ``n_trials`` zero-skill
    strategies whose trial Sharpes have variance ``var_trial_sr``.
    ``kurt`` is *raw* kurtosis (normal = 3). Values near 1 mean the
    Sharpe survives the multiple-testing haircut; near 0 means it is
    what you'd expect from trying many random things.
    """
    if n_trials < 1 or n_obs < 2:
        return float("nan")
    emc = 0.5772156649015329  # Euler-Mascheroni
    if n_trials == 1:
        sr_star = 0.0
    else:
        sd = float(np.sqrt(max(var_trial_sr, 0.0)))
        sr_star = sd * (
            (1 - emc) * stats.norm.ppf(1 - 1 / n_trials)
            + emc * stats.norm.ppf(1 - 1 / (n_trials * np.e))
        )
    denom = np.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr**2)
    if not np.isfinite(denom) or denom == 0:
        return float("nan")
    z = (sr - sr_star) * np.sqrt(n_obs - 1) / denom
    return float(stats.norm.cdf(z))
