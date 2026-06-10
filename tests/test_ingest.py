"""Phase 1 tests: ingestion, validation, parquet round-trip."""

import gzip
import json
from pathlib import Path

import pytest

from microstructure.ingest import BookSnapshot, iter_book_snapshots, iter_trades
from microstructure.parquet import build_book_parquet, build_trade_parquet, load_books, load_trades
from microstructure.quality import validate_books, validate_trades

T0 = 1_770_000_000.0  # fixed epoch base so hours are deterministic


def write_book_file(path: Path, records: list[dict]) -> None:
    with gzip.open(path, "at") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def book_rec(ts: float, symbol: str = "btcusdt", bid: float = 100.0, ask: float = 100.1) -> dict:
    return {
        "ts": ts,
        "symbol": symbol,
        "bids": [[str(bid), "1.0"], [str(bid - 0.1), "2.0"]],
        "asks": [[str(ask), "1.5"], [str(ask + 0.1), "2.5"]],
    }


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    write_book_file(
        tmp_path / "book-20260610-05.jsonl.gz",
        [book_rec(T0), book_rec(T0 + 1), book_rec(T0 + 2, symbol="ethusdt", bid=50, ask=50.05)],
    )
    with gzip.open(tmp_path / "trades-20260610-05.jsonl.gz", "at") as fh:
        fh.write(
            json.dumps(
                {"ts": T0, "symbol": "btcusdt", "price": "100.05", "qty": "0.5", "buyer_maker": True}
            )
            + "\n"
        )
        fh.write("{torn line")  # simulated crash mid-write
    return tmp_path


def test_iter_book_snapshots_parses_typed(data_dir: Path) -> None:
    snaps = list(iter_book_snapshots(data_dir))
    assert len(snaps) == 3
    s = snaps[0]
    assert isinstance(s, BookSnapshot)
    assert s.best_bid == 100.0
    assert s.best_ask == 100.1
    assert s.mid == pytest.approx(100.05)
    assert not s.is_crossed


def test_iter_trades_signed_qty_and_torn_line(data_dir: Path) -> None:
    trades = list(iter_trades(data_dir))
    assert len(trades) == 1  # torn line dropped
    assert trades[0].signed_qty == -0.5  # buyer_maker=True → sell aggressor


def test_truncated_gzip_tail_is_tolerated(tmp_path: Path) -> None:
    path = tmp_path / "book-20260610-06.jsonl.gz"
    write_book_file(path, [book_rec(T0)])
    raw = path.read_bytes()
    path.write_bytes(raw[: len(raw) - 7])  # chop the gzip stream mid-member
    # must not raise; data recovered before the truncation point is kept
    snaps = list(iter_book_snapshots(tmp_path))
    assert len(snaps) <= 1


def test_validate_books_flags_crossed_gap_backwards(tmp_path: Path) -> None:
    write_book_file(
        tmp_path / "book-20260610-05.jsonl.gz",
        [
            book_rec(T0),
            book_rec(T0 + 1, bid=101.0, ask=100.9),  # crossed
            book_rec(T0 + 0.5),  # backwards ts
            book_rec(T0 + 30),  # 29s gap
        ],
    )
    q = validate_books(iter_book_snapshots(tmp_path), gap_threshold_s=5.0)["btcusdt"]
    assert q.n_snapshots == 4
    assert q.n_crossed == 1
    assert q.n_backwards_ts == 1
    assert len(q.gaps) == 1
    assert q.gaps[0].seconds == pytest.approx(29.0)
    assert q.coverage == pytest.approx(1 - 29.0 / 30.0)


def test_parquet_round_trip(data_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "pq"
    written = build_book_parquet(data_dir, out)
    assert len(written) == 2  # btcusdt + ethusdt partitions
    df = load_books(out, "btcusdt")
    assert len(df) == 2
    assert df["bid_px_0"].iloc[0] == 100.0
    assert df["ask_qty_1"].iloc[0] == 2.5
    # levels beyond recorded depth are nan-padded
    assert df["bid_px_5"].isna().all()

    build_trade_parquet(data_dir, out)
    tdf = load_trades(out, "btcusdt")
    assert tdf["signed_qty"].iloc[0] == -0.5


def test_parquet_idempotent_and_grows(data_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "pq"
    build_book_parquet(data_dir, out)
    assert build_book_parquet(data_dir, out) == []  # second run: nothing to do
    # live hour grows → partition is rewritten
    write_book_file(data_dir / "book-20260610-05.jsonl.gz", [book_rec(T0 + 3)])
    rewritten = build_book_parquet(data_dir, out)
    assert len(rewritten) == 1
    assert len(load_books(out, "btcusdt")) == 3


def test_validate_trades_counts(data_dir: Path) -> None:
    assert validate_trades(iter_trades(data_dir)) == {"btcusdt": 1}
