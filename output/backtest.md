# Backtest: imbalance strategy family vs random null

_Data: 2026-06-10 05:03 → 09:58 UTC (~4.9 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Execution: taker-only, walk the displayed book, fills capped at displayed size, 10 bps taker fee per side, one-snapshot (~1 s) execution delay. Sharpe annualized from ~1 s bars.

| symbol | best cfg (θ/hold) | ann. Sharpe | deflated SR (9 trials) | trades | fees | max DD | random null Sharpe (μ±σ, 50 seeds) | random p95 |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 0.3/60s | -512.36 | 0.00 | 200 | $27.37 | -0.320% | -476.66 ± 20.88 | -437.04 |
| ETHUSDT | 0.3/60s | -456.12 | 0.00 | 202 | $19.28 | -0.223% | -446.54 ± 23.23 | -399.15 |
| SOLUSDT | 0.7/60s | -647.36 | 0.00 | 302 | $38.66 | -0.465% | -450.41 ± 24.20 | -413.36 |

![chart](backtest.png)

## What this data cannot support — read before believing any number

- **Single venue.** Cross-venue arbitrage and venue-latency effects are invisible; Binance.US is a thin venue whose top of book may follow larger venues.
- **1 s snapshots.** Everything between snapshots is unseen: queue dynamics, fleeting quotes, the actual sequence of trades vs book changes. Maker strategies are unmodelable — taker-only here.
- **One overnight session.** A US-night, low-volatility regime. No daytime liquidity, no news, no weekend. Any parameter chosen on this night is fit to this night.
- **Annualizing seconds-scale Sharpe** multiplies noise by ~5600; treat the column as a ranking statistic, not an expectation.
- **Fees dominate.** At 10 bps/side a round trip costs ~20 bps while the BTC spread is ~2 bps; any high-frequency signal must clear fees, which is why the deflated SR column is the honest one.