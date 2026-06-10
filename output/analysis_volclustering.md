# Volatility clustering and jumps

_Data: 2026-06-10 05:03 → 06:28 UTC (~1.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | mean ACF lags 1-5 | Ljung-Box p (10 lags) | median ann. vol | jump share of variance |
|---|---|---|---|---|
| BTCUSDT | +0.126 | 0.058 | 33.9% | 37.3% |
| ETHUSDT | +0.198 | 0.025 | 62.7% | 20.0% |
| SOLUSDT | +0.060 | 0.12 | 68.7% | 30.6% |

![chart](analysis_volclustering.png)

A small Ljung–Box p-value rejects 'RV is white noise' — the signature of volatility clustering. Jump share is max(RV − BV, 0)/RV summed over bars: bipower variation is jump-robust, so the excess of RV over BV estimates the discontinuous part. With one quiet overnight session, treat both as descriptive, not structural.