"""Phase 2 (night two) tests: venue ingestion, quality attribution, parquet."""

import gzip
import json
from pathlib import Path

import pytest

from microstructure.venue import (
    Heartbeat,
    VenueBook,
    build_venue_parquet,
    iter_venue_records,
    load_venue_books,
    venue_quality,
)

T0 = 1_781_000_000.0


def book_line(ts: float, venue: str = "kraken", symbol: str = "BTC-USD",
              bid: float = 100.0, ask: float = 100.1) -> dict:
    return {
        "ts": ts, "venue": venue, "symbol": symbol, "type": "book",
        "bids": [[bid, 1.0], [bid - 0.1, 2.0]],
        "asks": [[ask, 1.5], [ask + 0.1, 2.5]],
    }


def beat_line(ts: float, venue: str = "kraken", snapshots: int = 0,
              connected: bool = True) -> dict:
    return {
        "ts": ts, "venue": venue, "type": "heartbeat",
        "snapshots": snapshots, "connected": connected,
        "reconnects": 0, "uptime_s": 60.0,
    }


def write(path: Path, records: list[dict]) -> None:
    with gzip.open(path, "at") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def test_iter_separates_books_and_heartbeats(tmp_path: Path) -> None:
    write(tmp_path / "book-kraken-20260611-08.jsonl.gz",
          [book_line(T0), beat_line(T0 + 60, snapshots=1)])
    recs = list(iter_venue_records(tmp_path, "kraken"))
    assert isinstance(recs[0], VenueBook)
    assert recs[0].venue == "kraken"
    assert recs[0].symbol == "BTC-USD"
    assert recs[0].best_bid == 100.0
    assert isinstance(recs[1], Heartbeat)
    assert recs[1].connected


def test_crossed_and_locked_detected(tmp_path: Path) -> None:
    write(tmp_path / "book-kraken-20260611-08.jsonl.gz", [
        book_line(T0),
        book_line(T0 + 1, bid=100.2, ask=100.1),  # crossed
        book_line(T0 + 2, bid=100.1, ask=100.1),  # locked
    ])
    q = venue_quality(tmp_path, "kraken")["BTC-USD"]
    assert q.n_crossed == 1
    assert q.n_locked == 1


def test_gap_attribution_three_ways(tmp_path: Path) -> None:
    write(tmp_path / "book-kraken-20260611-08.jsonl.gz", [
        # gap 1: heartbeats present but disconnected -> feed-outage
        book_line(T0),
        beat_line(T0 + 30, snapshots=5, connected=False),
        book_line(T0 + 60),
        # gap 2: no heartbeats inside -> logger-down
        book_line(T0 + 300),
        # gap 3: heartbeats alive and counter advancing -> symbol-quiet
        beat_line(T0 + 320, snapshots=10),
        beat_line(T0 + 380, snapshots=200),
        book_line(T0 + 400),
    ])
    q = venue_quality(tmp_path, "kraken")["BTC-USD"]
    kinds = [g.attribution for g in q.gaps]
    assert kinds == ["feed-outage", "logger-down", "symbol-quiet"]
    assert q.gaps[0].seconds == pytest.approx(60.0)
    assert q.coverage == pytest.approx(1 - (60 + 240 + 100) / 400)


def test_cadence_stats(tmp_path: Path) -> None:
    write(tmp_path / "book-kraken-20260611-08.jsonl.gz",
          [book_line(T0 + i) for i in range(10)])
    med, p95 = venue_quality(tmp_path, "kraken")["BTC-USD"].cadence()
    assert med == pytest.approx(1.0)
    assert p95 == pytest.approx(1.0)


def test_venue_parquet_round_trip(tmp_path: Path) -> None:
    write(tmp_path / "book-kraken-20260611-08.jsonl.gz", [
        book_line(T0), book_line(T0 + 1),
        book_line(T0 + 2, symbol="ETH-USD", bid=50.0, ask=50.05),
        beat_line(T0 + 60, snapshots=3),  # must not become a parquet row
    ])
    write(tmp_path / "book-coinbase-20260611-08.jsonl.gz",
          [book_line(T0, venue="coinbase")])
    out = tmp_path / "pq"
    written = build_venue_parquet(tmp_path, out)
    assert len(written) == 3  # kraken BTC, kraken ETH, coinbase BTC
    df = load_venue_books(out, "kraken", "BTC-USD")
    assert len(df) == 2
    assert df["bid_px_0"].iloc[0] == 100.0
    assert df["bid_px_5"].isna().all()  # nan-padded beyond recorded depth
    with pytest.raises(FileNotFoundError):
        load_venue_books(out, "coinbase", "SOL-USD")
