# Backtest: imbalance strategy family vs random null

_Data: 2026-06-10 05:03 → 08:19 UTC (~3.3 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Execution: taker-only, walk the displayed book, fills capped at displayed size, 10 bps taker fee per side, one-snapshot (~1 s) execution delay. Sharpe annualized from ~1 s bars.

| symbol | best cfg (θ/hold) | ann. Sharpe | deflated SR (9 trials) | trades | fees | max DD | random null Sharpe (μ±σ, 50 seeds) | random p95 |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 0.3/60s | -507.82 | 0.00 | 117 | $16.59 | -0.203% | -482.90 ± 23.32 | -442.59 |
| ETHUSDT | 0.3/60s | -369.72 | 0.00 | 86 | $8.74 | -0.108% | -453.87 ± 25.53 | -411.78 |
| SOLUSDT | 0.7/60s | -653.47 | 0.00 | 192 | $24.67 | -0.300% | -456.84 ± 26.35 | -414.93 |

![chart](backtest.png)

## What this data cannot support — read before believing any number

- **Single venue.** Cross-venue arbitrage and venue-latency effects are invisible; Binance.US is a thin venue whose top of book may follow larger venues.
- **1 s snapshots.** Everything between snapshots is unseen: queue dynamics, fleeting quotes, the actual sequence of trades vs book changes. Maker strategies are unmodelable — taker-only here.
- **One overnight session.** A US-night, low-volatility regime. No daytime liquidity, no news, no weekend. Any parameter chosen on this night is fit to this night.
- **Annualizing seconds-scale Sharpe** multiplies noise by ~5600; treat the column as a ranking statistic, not an expectation.
- **Fees dominate.** At 10 bps/side a round trip costs ~20 bps while the BTC spread is ~2 bps; any high-frequency signal must clear fees, which is why the deflated SR column is the honest one.