# Backtest: imbalance strategy family vs random null

_Data: 2026-06-10 05:03 → 07:53 UTC (~2.8 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Execution: taker-only, walk the displayed book, fills capped at displayed size, 10 bps taker fee per side, one-snapshot (~1 s) execution delay. Sharpe annualized from ~1 s bars.

| symbol | best cfg (θ/hold) | ann. Sharpe | deflated SR (9 trials) | trades | fees | max DD | random null Sharpe (μ±σ, 50 seeds) | random p95 |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 0.3/60s | -527.38 | 0.00 | 101 | $14.37 | -0.178% | -486.92 ± 26.74 | -443.62 |
| ETHUSDT | 0.3/60s | -378.41 | 0.00 | 70 | $7.26 | -0.094% | -457.73 ± 30.72 | -411.51 |
| SOLUSDT | 0.7/60s | -653.88 | 0.00 | 159 | $20.43 | -0.253% | -461.94 ± 32.07 | -408.81 |

![chart](backtest.png)

## What this data cannot support — read before believing any number

- **Single venue.** Cross-venue arbitrage and venue-latency effects are invisible; Binance.US is a thin venue whose top of book may follow larger venues.
- **1 s snapshots.** Everything between snapshots is unseen: queue dynamics, fleeting quotes, the actual sequence of trades vs book changes. Maker strategies are unmodelable — taker-only here.
- **One overnight session.** A US-night, low-volatility regime. No daytime liquidity, no news, no weekend. Any parameter chosen on this night is fit to this night.
- **Annualizing seconds-scale Sharpe** multiplies noise by ~5600; treat the column as a ranking statistic, not an expectation.
- **Fees dominate.** At 10 bps/side a round trip costs ~20 bps while the BTC spread is ~2 bps; any high-frequency signal must clear fees, which is why the deflated SR column is the honest one.