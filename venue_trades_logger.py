#!/usr/bin/env python3
"""Multi-venue TRADE logger — companion to venue_logger.py (book capture).

Runs as a SEPARATE process so the long-running book loggers are never
touched: same architecture (hourly gzip jsonl, heartbeats, backoff,
give-up policy), parallel stream, public feeds only, read-only.

Run:  python3 venue_trades_logger.py kraken
      python3 venue_trades_logger.py coinbase

Unified schema (data/trades-{venue}-YYYYMMDD-HH.jsonl.gz):

  trade line:
    {"ts": <unix float, local receive time>, "venue": "kraken"|"coinbase",
     "symbol": "BTC-USD", "type": "trade", "trade_ts": <unix float,
     exchange event time>, "price": <num>, "qty": <num>,
     "side": "buy"|"sell", "trade_id": <str>}

  heartbeat line (every 60 s, also when disconnected):
    {"ts", "venue", "type": "heartbeat", "trades": <total written>,
     "connected", "reconnects", "uptime_s"}

SIDE SEMANTICS — read before using as an aggressor flag:
  * Kraken v2 `trade` channel documents `side` as the TAKER direction
    ("buy" = buyer was the aggressor). Recorded verbatim.
  * Coinbase Advanced Trade `market_trades` documents `side` only as
    "side of the trade"; community reports disagree about maker vs
    taker convention. Recorded verbatim (lowercased) — VALIDATE
    empirically against the simultaneous book capture (a trade printing
    at the prevailing ask is buyer-aggressed) before treating it as an
    aggressor flag. The H1 replication must do this validation first.

Both venues' trade channels replay a snapshot of recent history on
subscribe; those records predate the connection and would duplicate on
every reconnect, so snapshot-type events are NOT logged — only live
updates. (Gap cost: trades during a disconnect are lost, same blind
spot the book capture has.)

Rate-limit compliance: identical posture to venue_logger.py — one
long-lived connection per venue, one subscribe message (3 symbols),
nothing sent afterwards but protocol pings; backoff 1s -> 60s cap and
exit-nonzero after 30 consecutive failures.
"""

import asyncio
import gzip
import json
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import websockets

DATA_DIR = Path(__file__).parent / "data"
HEARTBEAT_INTERVAL = 60.0
MAX_CONSECUTIVE_RETRIES = 30

VENUES = {
    "kraken": {
        "url": "wss://ws.kraken.com/v2",
        "symbols": {"BTC/USD": "BTC-USD", "ETH/USD": "ETH-USD", "SOL/USD": "SOL-USD"},
    },
    "coinbase": {
        "url": "wss://advanced-trade-ws.coinbase.com",
        "symbols": {"BTC-USD": "BTC-USD", "ETH-USD": "ETH-USD", "SOL-USD": "SOL-USD"},
    },
}

shutdown = asyncio.Event()


class HourlyGzipWriter:
    """Appends JSON lines to data/trades-{venue}-YYYYMMDD-HH.jsonl.gz."""

    def __init__(self, venue: str):
        self.venue = venue
        self.current_hour = None
        self.fh = None

    def write(self, record: dict):
        hour = time.strftime("%Y%m%d-%H", time.gmtime())
        if hour != self.current_hour:
            if self.fh:
                self.fh.close()
            self.current_hour = hour
            path = DATA_DIR / f"trades-{self.venue}-{hour}.jsonl.gz"
            self.fh = gzip.open(path, "at")
        self.fh.write(json.dumps(record, separators=(",", ":")) + "\n")
        self.fh.flush()

    def close(self):
        if self.fh:
            self.fh.close()


class State:
    def __init__(self, venue: str):
        self.venue = venue
        self.trades = 0
        self.reconnects = 0
        self.connected = False
        self.started = time.time()


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def iso_to_unix(stamp: str) -> float:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()


# ---------------------------------------------------------------- kraken

async def run_kraken(ws, state: State, writer: HourlyGzipWriter):
    symbols = VENUES["kraken"]["symbols"]
    await ws.send(json.dumps({
        "method": "subscribe",
        "params": {"channel": "trade", "symbol": list(symbols)},
    }))
    while not shutdown.is_set():
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=120))
        if msg.get("channel") != "trade":
            continue  # status / ack / heartbeat
        if msg.get("type") == "snapshot":
            continue  # recent-history replay: would duplicate on reconnect
        ts = time.time()
        for d in msg.get("data", []):
            sym = symbols.get(d.get("symbol"))
            if sym is None:
                continue
            writer.write({
                "ts": ts,
                "venue": "kraken",
                "symbol": sym,
                "type": "trade",
                "trade_ts": iso_to_unix(d["timestamp"]),
                "price": float(d["price"]),
                "qty": float(d["qty"]),
                "side": str(d["side"]).lower(),  # documented: taker direction
                "trade_id": str(d.get("trade_id", "")),
            })
            state.trades += 1


# ---------------------------------------------------------------- coinbase

async def run_coinbase(ws, state: State, writer: HourlyGzipWriter):
    symbols = VENUES["coinbase"]["symbols"]
    await ws.send(json.dumps({
        "type": "subscribe",
        "product_ids": list(symbols),
        "channel": "market_trades",
    }))
    while not shutdown.is_set():
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=120))
        if msg.get("type") == "error" or msg.get("channel") == "error":
            raise RuntimeError(f"coinbase error message: {msg}")
        if msg.get("channel") != "market_trades":
            continue
        ts = time.time()
        for event in msg.get("events", []):
            if event.get("type") == "snapshot":
                continue  # recent-history replay
            for d in event.get("trades", []):
                sym = symbols.get(d.get("product_id"))
                if sym is None:
                    continue
                writer.write({
                    "ts": ts,
                    "venue": "coinbase",
                    "symbol": sym,
                    "type": "trade",
                    "trade_ts": iso_to_unix(d["time"]),
                    "price": float(d["price"]),
                    "qty": float(d["size"]),
                    # verbatim; maker/taker convention UNVALIDATED (docstring)
                    "side": str(d["side"]).lower(),
                    "trade_id": str(d.get("trade_id", "")),
                })
                state.trades += 1


# ---------------------------------------------------------------- shared

async def heartbeat_loop(state: State, writer: HourlyGzipWriter):
    while not shutdown.is_set():
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        writer.write({
            "ts": time.time(),
            "venue": state.venue,
            "type": "heartbeat",
            "trades": state.trades,
            "connected": state.connected,
            "reconnects": state.reconnects,
            "uptime_s": round(time.time() - state.started, 1),
        })
        log(f"heartbeat: {state.trades} trades, connected={state.connected}, "
            f"reconnects={state.reconnects}")


async def connection_loop(state: State, writer: HourlyGzipWriter):
    venue = VENUES[state.venue]
    handler = run_kraken if state.venue == "kraken" else run_coinbase
    backoff = 1
    consecutive_failures = 0
    while not shutdown.is_set():
        try:
            async with websockets.connect(
                venue["url"], ping_interval=20, max_size=32 * 1024 * 1024
            ) as ws:
                log(f"connected to {state.venue} trades")
                state.connected = True
                consecutive_failures = 0
                backoff = 1
                await handler(ws, state, writer)
        except asyncio.CancelledError:
            break
        except Exception as e:
            state.connected = False
            if shutdown.is_set():
                break
            consecutive_failures += 1
            state.reconnects += 1
            if consecutive_failures >= MAX_CONSECUTIVE_RETRIES:
                log(f"giving up after {consecutive_failures} consecutive failures: {e!r}")
                shutdown.set()
                return 1
            log(f"error: {e!r} — reconnect {consecutive_failures}/"
                f"{MAX_CONSECUTIVE_RETRIES} in {backoff}s")
            try:
                await asyncio.wait_for(shutdown.wait(), timeout=backoff)
            except asyncio.TimeoutError:
                pass
            backoff = min(backoff * 2, 60)
    state.connected = False
    return 0


async def run(state: State, writer: HourlyGzipWriter):
    hb = asyncio.create_task(heartbeat_loop(state, writer))
    rc = await connection_loop(state, writer)
    shutdown.set()
    hb.cancel()
    await asyncio.gather(hb, return_exceptions=True)
    log(f"stopped after {state.trades} trades")
    return rc


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in VENUES:
        print(f"usage: {sys.argv[0]} {{{'|'.join(VENUES)}}}", file=sys.stderr)
        return 2
    DATA_DIR.mkdir(exist_ok=True)
    state = State(sys.argv[1])
    writer = HourlyGzipWriter(state.venue)
    loop = asyncio.new_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown.set)
    try:
        return loop.run_until_complete(run(state, writer))
    finally:
        writer.close()
        loop.close()


if __name__ == "__main__":
    sys.exit(main())
