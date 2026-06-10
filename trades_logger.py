#!/usr/bin/env python3
"""Overnight trade-stream logger (companion to logger.py).

Connects to Binance.US trade streams and appends one JSON line per trade to
hourly-rotated gzip files data/trades-YYYYMMDD-HH.jsonl.gz.

Fields: ts (exchange event time, s), symbol, price, qty, buyer_maker
(True = sell aggressor hit the bid; False = buy aggressor lifted the ask).

Run:  python3 trades_logger.py
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
    f"{s}@trade" for s in SYMBOLS
)
DATA_DIR = Path(__file__).parent / "data"

shutdown = asyncio.Event()


class HourlyGzipWriter:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.current_hour = None
        self.fh = None

    def write(self, record: dict):
        hour = time.strftime("%Y%m%d-%H", time.gmtime())
        if hour != self.current_hour:
            if self.fh:
                self.fh.close()
            self.current_hour = hour
            self.fh = gzip.open(DATA_DIR / f"{self.prefix}-{hour}.jsonl.gz", "at")
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
                    msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=120))
                    d = msg["data"]
                    writer.write(
                        {
                            "ts": d["E"] / 1000,
                            "symbol": d["s"].lower(),
                            "price": d["p"],
                            "qty": d["q"],
                            "buyer_maker": d["m"],
                        }
                    )
                    n += 1
                    if time.time() - last_report > 300:
                        print(
                            f"[{time.strftime('%H:%M:%S')}] {n} trades logged",
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
    print(f"[{time.strftime('%H:%M:%S')}] stopped after {n} trades", flush=True)


def main():
    DATA_DIR.mkdir(exist_ok=True)
    writer = HourlyGzipWriter("trades")
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
