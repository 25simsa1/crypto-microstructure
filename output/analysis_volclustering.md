# Volatility clustering and jumps

_Data: 2026-06-10 05:03 → 05:58 UTC (~0.9 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | mean ACF lags 1-5 | Ljung-Box p (10 lags) | median ann. vol | jump share of variance |
|---|---|---|---|---|
| BTCUSDT | +0.020 | 0.96 | 33.9% | 35.7% |
| ETHUSDT | +0.183 | 0.28 | 64.8% | 18.7% |
| SOLUSDT | +0.023 | 0.07 | 70.7% | 29.0% |

![chart](analysis_volclustering.png)

A small Ljung–Box p-value rejects 'RV is white noise' — the signature of volatility clustering. Jump share is max(RV − BV, 0)/RV summed over bars: bipower variation is jump-robust, so the excess of RV over BV estimates the discontinuous part. With one quiet overnight session, treat both as descriptive, not structural.