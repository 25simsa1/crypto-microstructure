# Volatility clustering and jumps

_Data: 2026-06-10 05:03 → 11:17 UTC (~6.2 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | mean ACF lags 1-5 | Ljung-Box p (10 lags) | median ann. vol | jump share of variance |
|---|---|---|---|---|
| BTCUSDT | +0.096 | 0.41 | 42.9% | 36.0% |
| ETHUSDT | +0.063 | 0.99 | 60.9% | 29.4% |
| SOLUSDT | -0.015 | 1 | 66.5% | 39.8% |

![chart](analysis_volclustering.png)

A small Ljung–Box p-value rejects 'RV is white noise' — the signature of volatility clustering. Jump share is max(RV − BV, 0)/RV summed over bars: bipower variation is jump-robust, so the excess of RV over BV estimates the discontinuous part. With one quiet overnight session, treat both as descriptive, not structural.