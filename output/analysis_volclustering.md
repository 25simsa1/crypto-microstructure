# Volatility clustering and jumps

_Data: 2026-06-10 05:03 → 08:52 UTC (~3.8 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | mean ACF lags 1-5 | Ljung-Box p (10 lags) | median ann. vol | jump share of variance |
|---|---|---|---|---|
| BTCUSDT | +0.310 | 8.2e-41 | 40.9% | 29.2% |
| ETHUSDT | +0.098 | 0.034 | 57.9% | 22.9% |
| SOLUSDT | +0.091 | 0.0014 | 66.1% | 34.9% |

![chart](analysis_volclustering.png)

A small Ljung–Box p-value rejects 'RV is white noise' — the signature of volatility clustering. Jump share is max(RV − BV, 0)/RV summed over bars: bipower variation is jump-robust, so the excess of RV over BV estimates the discontinuous part. With one quiet overnight session, treat both as descriptive, not structural.