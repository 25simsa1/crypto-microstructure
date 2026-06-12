"""Trade-side classifier and quote-join tests (hand-constructed cases)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from validate_trade_side import classify, prevailing_quote

BID, ASK = 100.0, 100.10


def test_classify_at_and_above_ask_is_buy() -> None:
    assert classify(100.10, BID, ASK) == "buy"
    assert classify(100.50, BID, ASK) == "buy"


def test_classify_at_and_below_bid_is_sell() -> None:
    assert classify(100.0, BID, ASK) == "sell"
    assert classify(99.50, BID, ASK) == "sell"


def test_classify_inside_spread_is_unclassifiable() -> None:
    assert classify(100.05, BID, ASK) is None


def test_prevailing_quote_picks_latest_at_or_before() -> None:
    ts = [10.0, 11.0, 12.0]
    quotes = [(99.0, 99.1), (100.0, 100.1), (101.0, 101.1)]
    bid, ask, age = prevailing_quote(ts, quotes, 11.4)
    assert (bid, ask) == (100.0, 100.1)
    assert age == pytest.approx(0.4)
    # exactly at a snapshot timestamp: that snapshot prevails
    bid, ask, age = prevailing_quote(ts, quotes, 12.0)
    assert (bid, ask) == (101.0, 101.1)
    assert age == 0.0


def test_prevailing_quote_stale_or_missing_is_discarded() -> None:
    ts = [10.0]
    quotes = [(100.0, 100.1)]
    # quote older than the max age: unjoinable
    assert prevailing_quote(ts, quotes, 13.5, max_age_s=2.0) is None
    # trade before any quote exists: unjoinable
    assert prevailing_quote(ts, quotes, 9.0) is None
