# Night Log — 2026-06-10

Running record of the overnight shift. Newest entries at the bottom.

## 01:03 PT — Book logger launched
- `logger.py` connected to Binance.US depth20@1000ms for BTC/ETH/SOL under `caffeinate -i`.

## 01:08 PT — Iteration 1
**Health:** book logger alive (pid 54556), data growing normally (~10 KB/min compressed).

**Bug fixed:** `analyze.py` crashed with `EOFError` when reading the gzip file the logger is still writing (truncated tail). Now reads line-by-line and stops cleanly at the unflushed tail.

**First-pass findings (4 min of data, ~22:05 PT):**
- Quoted spreads: BTC ~1.9 bps, ETH ~2.5 bps, SOL ~4.5 bps (mean). BTC p95 only 2.9 bps — tight and stable; ETH p95 5.7 bps shows occasional widening.
- Book imbalance is ask-heavy across all three (BTC −0.13, ETH −0.35, SOL −0.06 within ±0.1% of mid). ETH notably lopsided — worth watching whether that persists or predicts drift.
- Realized vol (1-min, annualized): BTC 2.1%, ETH 4.3%, SOL 5.6% — very quiet US-night regime so far.
- Depth within ±0.1% of mid: BTC ~$200k total, SOL only ~$17k — SOL's near-touch book is thin; its liquidity lives further out (~$480k within ±0.5%).

**Extension built:** `trades_logger.py` — separate process logging every trade (price, qty, aggressor side) for the same symbols. Launched 01:08 PT. This enables order-flow imbalance, effective-spread, and price-impact metrics.

**Roadmap for remaining iterations (hedge-fund-grade build-out):**
1. ~~Trade stream~~ ✅
2. Cross-venue top-of-book poller (Coinbase + Kraken REST) → lead-lag / price-discovery analysis across venues
3. `metrics.py` library: microprice, order-flow imbalance (OFI), effective vs quoted spread, trade-sign autocorrelation, price impact (Kyle-lambda style regression), Amihud illiquidity
4. Anomaly detection pass: spread spikes, depth evaporation events, vol regime shifts → flagged in this log
5. Self-regenerating HTML dashboard (`dashboard.html`)
6. Time-of-night seasonality analysis (does liquidity die at a specific hour?)
7. Final deliverable: `RESEARCH.md` — a structured research note with figures, written like a desk note

## 01:45 PT — All five phases of the platform build complete
- Phase 1-5 done and committed: typed data layer + parquet store, hand-tested feature library, four statistical studies, anti-lookahead backtester with deflated Sharpe + random null, README/Makefile/FINDINGS, ruff + strict mypy + 23 tests green.
- Honest results so far: no imbalance feature clears the Bonferroni bar; no lead-lag beyond lag 0; all strategies lose to fees (deflated SR 0.00) — as they should on 2 bps spreads with 10 bps taker fees.
- Rest of night: rerun `make all` as data grows; build trade-tape features (effective spread, trade-sign autocorrelation); refresh FINDINGS near morning.

## 02:05 PT — Iteration: trade-tape features
- `make all` refreshed on ~3.2k snaps/symbol. Quality layer caught its first real gap: SOL coverage 99.26% (one short disconnect). BTC/ETH still 100%.
- Built `effective_spread_bps`, `trade_sign_autocorr`, `volume_bars` with hand-computed tests. Found and fixed a real float bug: cumsum hitting 1.999...8 instead of 2.0 pushed bucket-boundary trades into the wrong volume bar.
- First tape findings (~60-75 trades/symbol — thin overnight tape): effective spread < quoted everywhere (SOL: 1.56 vs 3.13 bps — trades print well inside the touch), sign autocorrelation near zero at these counts, nothing like the textbook long memory yet. Needs the full night's tape.

## 02:30 PT — Iteration: Epps effect
- ~4.9k snaps/symbol now; SOL coverage 99.41% (its earlier gap shrinking as a share of the night), BTC/ETH still perfect.
- New study `analysis_epps.py`, wired into Makefile + FINDINGS: pairwise correlation vs sampling interval (1s → 300s). Result is textbook: BTC/ETH goes 0.34 @ 1s → 0.94 @ 300s, with half the long-run correlation already there by ~2s. Cross-asset information on this venue propagates fast, but 1s returns still mostly miss it — quantifies why the lead-lag study found nothing at 1s resolution.

## 02:58 PT — Iteration: tape analysis wired in
- ~6.5k snaps/symbol; all three symbols show one ~5s reconnect blip (99.9% coverage) — the quality report catches it.
- New `analysis_tape.py` in Makefile + FINDINGS: effective vs quoted spread, sign-ACF with null band, volume-bar flow-vs-return scatter.
- SOL is the interesting one: effective spread half the quoted (1.57 vs 3.12 bps — takers time their entries inside the wide touch) and sign ACF +0.21 over lags 1-5, the first hint of order-flow memory. BTC/ETH tape still looks memoryless at these counts.

## 03:30 PT — Iteration: anomaly detection
- New `anomaly.py` (trailing median+MAD episodes, past-only) + `analysis_anomalies.py` wired into Makefile/FINDINGS, with tests on synthetic books with planted events.
- Two real tuning lessons: (1) MAD needs a double warmup (median first, then deviations) which silently NaN'd the vol detector — made min_periods explicit; (2) MAD-based z on tick-quantized spreads flags routine one-tick flickers (376 "episodes"!) — switched spread/depth to multiplicative thresholds with a 3s minimum duration → 9 genuine episodes: ETH 6 spread blowouts (to ~10-12 bps) + 1 depth evaporation, BTC/SOL one vol shift each.

## 04:00 PT — Iteration: order-flow memory significance
- Added Ljung-Box (10 lags) + Wald-Wolfowitz runs test to the tape analysis, with sanity tests for the runs statistic.
- SOL's sign memory survived the thicker tape: LB p < 0.001, ACF lags 1-5 = +0.15 — genuine (one-night) order-flow persistence. BTC/ETH instead show mild *alternation* (runs z ≈ +2), i.e. bid-ask bounce.
- Honest correction: SOL's "effective spread at half the quoted" from the 60-trade tape vanished at 206 trades (3.10 vs 3.12 bps). Early-night descriptive stats don't survive; this is why everything re-runs on the full capture.

## 04:25 PT — Iteration: report polish
- 11.3k snaps/symbol, 2.4 MB raw. Coverage steady (SOL 99.37% remains the worst, all from a few reconnects).
- README architecture/diagram updated for the 7 studies + anomaly module; rewrote MORNING.md as the actual morning report: three headline results, overnight decisions, and the four questions that need Simon (continue capture? publish to GitHub? real fee tier? next direction?).
