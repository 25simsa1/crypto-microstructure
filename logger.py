#!/usr/bin/env python3
"""Overnight crypto order-book logger.

Connects to Binance.US partial-book-depth streams (top 20 levels, 1s updates)
and appends one JSON line per snapshot to hourly-rotated gzip files in data/.

Run:  python3 logger.py
Stop: Ctrl-C (files are flushed on every write, so a crash loses nothing).
"""

import asyncio
import gzip
import json
import signal
import sys
import time
from pathlib import Path

import websockets

SYMBOLS = ["btcusdt", "ethusdt", "solusdt"]
STREAM_URL = "wss://stream.binance.us:9443/stream?streams=" + "/".join(
    f"{s}@depth20@1000ms" for s in SYMBOLS
)
DATA_DIR = Path(__file__).parent / "data"

shutdown = asyncio.Event()


class HourlyGzipWriter:
    """Appends JSON lines to data/book-YYYYMMDD-HH.jsonl.gz, rotating hourly."""

    def __init__(self):
        self.current_hour = None
        self.fh = None

    def write(self, record: dict):
        hour = time.strftime("%Y%m%d-%H", time.gmtime())
        if hour != self.current_hour:
            if self.fh:
                self.fh.close()
            self.current_hour = hour
            path = DATA_DIR / f"book-{hour}.jsonl.gz"
            self.fh = gzip.open(path, "at")
        self.fh.write(json.dumps(record, separators=(",", ":")) + "\n")
        self.fh.flush()

    def close(self):
        if self.fh:
            self.fh.close()


async def run(writer: HourlyGzipWriter):
    n = 0
    last_report = time.time()
    backoff = 1
    while not shutdown.is_set():
        try:
            async with websockets.connect(STREAM_URL, ping_interval=20) as ws:
                print(f"[{time.strftime('%H:%M:%S')}] connected", flush=True)
                backoff = 1
                while not shutdown.is_set():
                    msg = json.loads(
                        await asyncio.wait_for(ws.recv(), timeout=30)
                    )
                    stream, data = msg["stream"], msg["data"]
                    writer.write(
                        {
                            "ts": time.time(),
                            "symbol": stream.split("@")[0],
                            "bids": data["bids"],  # [[price, qty], ...] best first
                            "asks": data["asks"],
                        }
                    )
                    n += 1
                    if time.time() - last_report > 300:
                        print(
                            f"[{time.strftime('%H:%M:%S')}] {n} snapshots logged",
                            flush=True,
                        )
                        last_report = time.time()
        except asyncio.CancelledError:
            break
        except Exception as e:
            if shutdown.is_set():
                break
            print(
                f"[{time.strftime('%H:%M:%S')}] error: {e!r} — reconnecting in {backoff}s",
                flush=True,
            )
            try:
                await asyncio.wait_for(shutdown.wait(), timeout=backoff)
            except asyncio.TimeoutError:
                pass
            backoff = min(backoff * 2, 60)
    print(f"[{time.strftime('%H:%M:%S')}] stopped after {n} snapshots", flush=True)


def main():
    DATA_DIR.mkdir(exist_ok=True)
    writer = HourlyGzipWriter()
    loop = asyncio.new_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown.set)
    try:
        loop.run_until_complete(run(writer))
    finally:
        writer.close()
        loop.close()


if __name__ == "__main__":
    sys.exit(main())
