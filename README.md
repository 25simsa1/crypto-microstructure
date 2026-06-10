# crypto-microstructure

A market microstructure research platform built over one night of live
Binance.US data: top-20 order book snapshots (~1/s) and the full trade
tape for BTC, ETH and SOL, captured by two small websocket loggers and
turned into a typed, tested, reproducible research pipeline.

The point is not a trading strategy — the backtest section concludes,
honestly, that no strategy in the tested family survives fees on this
data. The point is the *methodology*: clean data layer, hand-verified
feature definitions, statistics that punish multiple testing, and a
backtester that physically cannot look ahead.

## Architecture

```
            live capture (runs unattended)
  ┌─────────────────────────────────────────────┐
  │  logger.py            trades_logger.py      │
  │  book snapshots 1/s   every trade           │
  │        └──────┬──────────────┘              │
  │               ▼                             │
  │  data/book-*.jsonl.gz, trades-*.jsonl.gz    │  hourly-rotated, gzip,
  └───────────────┬─────────────────────────────┘  flushed every write
                  ▼
        src/microstructure/
  ┌─────────────────────────────────────────────┐
  │ ingest.py    typed parsing, live-file safe  │
  │ quality.py   gaps / crossed books / report  │
  │ parquet.py   symbol-hour partitioned store  │
  │ features.py  microprice, OFI, imbalance,    │
  │              RV / Parkinson / bipower       │
  │ anomaly.py   spread/depth/vol episode flags │
  │ backtest.py  event replay, walk-the-book    │
  │              fills, deflated Sharpe         │
  │ analysis.py  shared plotting/loading        │
  └───────────────┬─────────────────────────────┘
                  ▼
              scripts/            output/
  build_data.py ──────────────▶ data_quality.md
  analysis_*.py (7 studies) ──▶ *.png + *.md
  run_backtest.py ────────────▶ backtest.md
  build_findings.py ──────────▶ ../FINDINGS.md
```

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
make all     # parquet + quality report + 7 studies + backtest + FINDINGS.md
make check   # ruff + mypy --strict + pytest
```

The loggers (`logger.py`, `trades_logger.py`, stdlib + `websockets` only)
run separately: `caffeinate -i python3 logger.py`.

## What's inside

| module | what it does | the detail that matters |
|---|---|---|
| `ingest.py` | jsonl.gz → typed dataclasses | tolerates truncated gzip tails from live files |
| `quality.py` | validation | gaps, crossed books, backwards timestamps — known before any analysis |
| `parquet.py` | columnar store | idempotent; only rewrites partitions that grew |
| `features.py` | feature library | every formula stated in the docstring, unit-tested against hand-computed numbers |
| `anomaly.py` | episode detection | trailing-robust thresholds tuned on real tick-quantized data, not textbook z-scores |
| `backtest.py` | event-driven replay | decisions at snapshot *t* execute against snapshot *t+1* — lookahead is structurally impossible |

## Honesty constraints

- Imbalance/return regressions use Newey–West errors and a Bonferroni
  bar across all 27 hypotheses tested.
- The backtest pays taker fees, crosses the spread, and cannot fill more
  than displayed size; its Sharpe is deflated for the 9 configs tried
  and compared against 50 random-strategy seeds.
- Every report carries a data-span note; `FINDINGS.md` opens with what
  one night of single-venue snapshots cannot support.

## Results

See [FINDINGS.md](FINDINGS.md) — regenerated from the full capture by
`make all`.
