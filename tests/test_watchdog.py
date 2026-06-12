"""Content-freeze detection in the watchdog (the failure mtime checks miss)."""

import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from logger_watchdog import content_freeze

T0 = 1_781_300_000.0


def write_books(path: Path, tops: list[tuple[float, float]], t0: float = T0) -> None:
    with gzip.open(path, "at") as fh:
        for i, (bid, ask) in enumerate(tops):
            fh.write(json.dumps({
                "ts": t0 + i, "venue": "coinbase", "symbol": "ETH-USD",
                "type": "book", "bids": [[bid, 1.0]], "asks": [[ask, 1.0]],
            }) + "\n")


def test_frozen_content_detected(tmp_path: Path) -> None:
    # 400 identical snapshots arriving on schedule = frozen
    write_books(tmp_path / "book-coinbase-20260612-20.jsonl.gz",
                [(100.0, 100.1)] * 400)
    frozen = content_freeze("coinbase", data_dir=tmp_path)
    assert "ETH-USD" in frozen
    assert frozen["ETH-USD"] >= 300


def test_live_content_clean(tmp_path: Path) -> None:
    # mid moves every 10 snapshots: never frozen
    tops = [(100.0 + (i // 10) * 0.1, 100.1 + (i // 10) * 0.1) for i in range(400)]
    write_books(tmp_path / "book-coinbase-20260612-20.jsonl.gz", tops)
    assert content_freeze("coinbase", data_dir=tmp_path) == {}


def test_data_gap_is_not_a_freeze(tmp_path: Path) -> None:
    # 20 snapshots, then nothing: unchanged content but snapshots NOT arriving
    write_books(tmp_path / "book-coinbase-20260612-20.jsonl.gz",
                [(100.0, 100.1)] * 20)
    assert content_freeze("coinbase", data_dir=tmp_path) == {}


def test_freeze_straddling_hourly_rotation(tmp_path: Path) -> None:
    write_books(tmp_path / "book-coinbase-20260612-20.jsonl.gz",
                [(100.0, 100.1)] * 200, t0=T0)
    write_books(tmp_path / "book-coinbase-20260612-21.jsonl.gz",
                [(100.0, 100.1)] * 200, t0=T0 + 200)
    frozen = content_freeze("coinbase", data_dir=tmp_path)
    assert frozen.get("ETH-USD", 0) >= 300
