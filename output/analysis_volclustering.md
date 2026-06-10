# Volatility clustering and jumps

_Data: 2026-06-10 05:03 → 09:25 UTC (~4.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | mean ACF lags 1-5 | Ljung-Box p (10 lags) | median ann. vol | jump share of variance |
|---|---|---|---|---|
| BTCUSDT | +0.213 | 5.5e-20 | 43.1% | 28.9% |
| ETHUSDT | +0.136 | 4.8e-05 | 59.9% | 21.7% |
| SOLUSDT | +0.078 | 0.0023 | 66.4% | 34.7% |

![chart](analysis_volclustering.png)

A small Ljung–Box p-value rejects 'RV is white noise' — the signature of volatility clustering. Jump share is max(RV − BV, 0)/RV summed over bars: bipower variation is jump-robust, so the excess of RV over BV estimates the discontinuous part. With one quiet overnight session, treat both as descriptive, not structural.