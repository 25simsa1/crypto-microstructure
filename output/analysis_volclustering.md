# Volatility clustering and jumps

_Data: 2026-06-10 05:03 → 05:25 UTC (~0.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | mean ACF lags 1-5 | Ljung-Box p (10 lags) | median ann. vol | jump share of variance |
|---|---|---|---|---|
| BTCUSDT | -0.083 | 0.88 | 34.8% | 36.0% |
| ETHUSDT | +0.050 | 0.64 | 64.9% | 19.1% |
| SOLUSDT | -0.139 | 0.18 | 70.6% | 33.3% |

![chart](analysis_volclustering.png)

A small Ljung–Box p-value rejects 'RV is white noise' — the signature of volatility clustering. Jump share is max(RV − BV, 0)/RV summed over bars: bipower variation is jump-robust, so the excess of RV over BV estimates the discontinuous part. With one quiet overnight session, treat both as descriptive, not structural.