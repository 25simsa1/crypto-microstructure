# Volatility clustering and jumps

_Data: 2026-06-10 05:03 → 09:58 UTC (~4.9 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | mean ACF lags 1-5 | Ljung-Box p (10 lags) | median ann. vol | jump share of variance |
|---|---|---|---|---|
| BTCUSDT | +0.228 | 2.7e-26 | 43.1% | 29.4% |
| ETHUSDT | +0.147 | 2.9e-07 | 60.8% | 21.0% |
| SOLUSDT | +0.078 | 0.0014 | 67.2% | 32.5% |

![chart](analysis_volclustering.png)

A small Ljung–Box p-value rejects 'RV is white noise' — the signature of volatility clustering. Jump share is max(RV − BV, 0)/RV summed over bars: bipower variation is jump-robust, so the excess of RV over BV estimates the discontinuous part. With one quiet overnight session, treat both as descriptive, not structural.