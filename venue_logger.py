#!/usr/bin/env python3
"""Multi-venue order-book logger (Phase 1: cross-venue capture).

Connects to one venue's public websocket book feed (no API key, read-only),
maintains a local order book per symbol from the venue's snapshot+delta
stream, and emits a top-20 snapshot per symbol once per second — the same
shape as the old Binance.US capture — to hourly-rotated gzip jsonl files.

Run:  python3 venue_logger.py kraken
      python3 venue_logger.py coinbase
Stop: SIGINT/SIGTERM (files are flushed on every write, a crash loses nothing).

Unified schema (one JSON line per record, data/book-{venue}-YYYYMMDD-HH.jsonl.gz):

  book line:
    {"ts": <unix float>, "venue": "kraken"|"coinbase", "symbol": "BTC-USD",
     "type": "book", "bids": [[price, qty], ...], "asks": [[price, qty], ...]}
    bids best-first (desc), asks best-first (asc), up to 20 levels,
    prices/qtys as JSON numbers.

  heartbeat line (every 60 s, also when disconnected):
    {"ts": ..., "venue": ..., "type": "heartbeat", "snapshots": <total written>,
     "connected": <bool>, "reconnects": <total>, "uptime_s": <float>}

Rate-limit compliance (documented per venue, both feeds are public/unauthed):

  Kraken (docs.kraken.com/api/docs/guides/spot-ws-intro):
    Kraken limits websocket *connection attempts* (~150 per rolling 10 min
    per IP) and counts subscription requests against a generous per-connection
    budget. This logger holds exactly ONE long-lived connection with ONE
    subscribe message (3 symbols in a single request). On failure it
    reconnects with exponential backoff 1s -> 60s cap, i.e. worst case
    ~14 attempts per 10 minutes — two orders of magnitude under the limit.

  Coinbase Advanced Trade WS (docs.cdp.coinbase.com/advanced-trade/docs/ws-overview):
    The public market-data endpoint (advanced-trade-ws.coinbase.com) needs no
    auth for the level2 channel. Documented limits are on inbound client
    messages (subscribe requests, single-digit per second per IP) and
    connections; this logger holds ONE connection and sends ONE subscribe
    message per connection (3 products in a single request), then only reads.
    Same 1s -> 60s backoff. (The legacy Exchange feed ws-feed.exchange.
    coinbase.com is unreachable from this network — probed 2026-06-10 — which
    is why the Advanced Trade endpoint is used.)

  Neither venue's public book feed has a per-message read limit for
  subscribers; we never send anything after the initial subscribe except
  protocol-level pings (websockets library, every 20 s — both venues allow
  standard ping/pong keepalive).

Failure policy: after MAX_CONSECUTIVE_RETRIES (30) failed reconnects in a row
(~28 minutes at the backoff cap) the process exits non-zero rather than
retrying forever — a persistent outage should be visible, not silently spun on.
"""

import asyncio
import gzip
import json
import signal
import sys
import time
from pathlib import Path

import websockets

DATA_DIR = Path(__file__).parent / "data"
DEPTH_OUT = 20            # levels per side written per snapshot
SNAPSHOT_INTERVAL = 1.0   # seconds between emitted book snapshots
HEARTBEAT_INTERVAL = 60.0
MAX_CONSECUTIVE_RETRIES = 30
KRAKEN_DEPTH = 25         # subscription depth (>= DEPTH_OUT)

VENUES = {
    "kraken": {
        "url": "wss://ws.kraken.com/v2",
        # venue symbol -> unified symbol
        "symbols": {"BTC/USD": "BTC-USD", "ETH/USD": "ETH-USD", "SOL/USD": "SOL-USD"},
    },
    "coinbase": {
        "url": "wss://advanced-trade-ws.coinbase.com",
        "symbols": {"BTC-USD": "BTC-USD", "ETH-USD": "ETH-USD", "SOL-USD": "SOL-USD"},
    },
}

shutdown = asyncio.Event()


class HourlyGzipWriter:
    """Appends JSON lines to data/book-{venue}-YYYYMMDD-HH.jsonl.gz, rotating hourly."""

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
            path = DATA_DIR / f"book-{self.venue}-{hour}.jsonl.gz"
            self.fh = gzip.open(path, "at")
        self.fh.write(json.dumps(record, separators=(",", ":")) + "\n")
        self.fh.flush()

    def close(self):
        if self.fh:
            self.fh.close()


class State:
    def __init__(self, venue: str):
        self.venue = venue
        # unified symbol -> {"bids": {price: qty}, "asks": {price: qty}}
        self.books: dict[str, dict] = {}
        self.snapshots = 0
        self.reconnects = 0
        self.connected = False
        self.started = time.time()

    def clear_books(self):
        self.books.clear()


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------- kraken

async def run_kraken(ws, state: State):
    symbols = VENUES["kraken"]["symbols"]
    await ws.send(json.dumps({
        "method": "subscribe",
        "params": {"channel": "book", "symbol": list(symbols), "depth": KRAKEN_DEPTH},
    }))
    while not shutdown.is_set():
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
        if msg.get("channel") != "book":
            continue  # status / heartbeat / subscribe ack
        for d in msg.get("data", []):
            sym = symbols.get(d.get("symbol"))
            if sym is None:
                continue
            if msg.get("type") == "snapshot":
                state.books[sym] = {
                    "bids": {lvl["price"]: lvl["qty"] for lvl in d["bids"]},
                    "asks": {lvl["price"]: lvl["qty"] for lvl in d["asks"]},
                }
            else:  # update
                book = state.books.get(sym)
                if book is None:
                    continue
                for side in ("bids", "asks"):
                    for lvl in d.get(side, []):
                        if lvl["qty"] == 0:
                            book[side].pop(lvl["price"], None)
                        else:
                            book[side][lvl["price"]] = lvl["qty"]
                # keep only the subscribed depth so stale far levels can't linger
                book["bids"] = dict(sorted(book["bids"].items(), reverse=True)[:KRAKEN_DEPTH])
                book["asks"] = dict(sorted(book["asks"].items())[:KRAKEN_DEPTH])


# ---------------------------------------------------------------- coinbase

async def run_coinbase(ws, state: State):
    symbols = VENUES["coinbase"]["symbols"]
    await ws.send(json.dumps({
        "type": "subscribe",
        "product_ids": list(symbols),
        "channel": "level2",
    }))
    while not shutdown.is_set():
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
        if msg.get("type") == "error" or msg.get("channel") == "error":
            raise RuntimeError(f"coinbase error message: {msg}")
        if msg.get("channel") != "l2_data":
            continue  # subscriptions ack etc.
        for event in msg.get("events", []):
            sym = symbols.get(event.get("product_id"))
            if sym is None:
                continue
            if event.get("type") == "snapshot":
                state.books[sym] = {"bids": {}, "asks": {}}
            book = state.books.get(sym)
            if book is None:
                continue
            for upd in event.get("updates", []):
                key = "bids" if upd["side"] == "bid" else "asks"
                price = float(upd["price_level"])
                qty = float(upd["new_quantity"])
                if qty == 0:
                    book[key].pop(price, None)
                else:
                    book[key][price] = qty


# ---------------------------------------------------------------- shared

async def snapshot_loop(state: State, writer: HourlyGzipWriter):
    while not shutdown.is_set():
        await asyncio.sleep(SNAPSHOT_INTERVAL)
        ts = time.time()
        for sym, book in state.books.items():
            bids = sorted(book["bids"].items(), reverse=True)[:DEPTH_OUT]
            asks = sorted(book["asks"].items())[:DEPTH_OUT]
            if not bids or not asks:
                continue
            writer.write({
                "ts": ts,
                "venue": state.venue,
                "symbol": sym,
                "type": "book",
                "bids": [[p, q] for p, q in bids],
                "asks": [[p, q] for p, q in asks],
            })
            state.snapshots += 1


async def heartbeat_loop(state: State, writer: HourlyGzipWriter):
    while not shutdown.is_set():
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        hb = {
            "ts": time.time(),
            "venue": state.venue,
            "type": "heartbeat",
            "snapshots": state.snapshots,
            "connected": state.connected,
            "reconnects": state.reconnects,
            "uptime_s": round(time.time() - state.started, 1),
        }
        writer.write(hb)
        log(f"heartbeat: {state.snapshots} snapshots, connected={state.connected}, "
            f"reconnects={state.reconnects}")


async def connection_loop(state: State):
    venue = VENUES[state.venue]
    handler = run_kraken if state.venue == "kraken" else run_coinbase
    backoff = 1
    consecutive_failures = 0
    while not shutdown.is_set():
        try:
            # max_size: the Coinbase level2 snapshot is a single >1 MiB frame
            async with websockets.connect(
                venue["url"], ping_interval=20, max_size=32 * 1024 * 1024
            ) as ws:
                log(f"connected to {state.venue}")
                state.connected = True
                consecutive_failures = 0
                backoff = 1
                await handler(ws, state)
        except asyncio.CancelledError:
            break
        except Exception as e:
            state.connected = False
            state.clear_books()  # never snapshot a stale book across a reconnect
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
    tasks = [
        asyncio.create_task(snapshot_loop(state, writer)),
        asyncio.create_task(heartbeat_loop(state, writer)),
    ]
    rc = await connection_loop(state)
    shutdown.set()
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    log(f"stopped after {state.snapshots} snapshots")
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
