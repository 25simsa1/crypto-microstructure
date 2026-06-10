# Volatility clustering and jumps

_Data: 2026-06-10 05:03 → 08:19 UTC (~3.3 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | mean ACF lags 1-5 | Ljung-Box p (10 lags) | median ann. vol | jump share of variance |
|---|---|---|---|---|
| BTCUSDT | +0.316 | 2.8e-29 | 38.3% | 31.6% |
| ETHUSDT | +0.083 | 0.011 | 57.4% | 23.5% |
| SOLUSDT | +0.040 | 0.0044 | 64.2% | 33.5% |

![chart](analysis_volclustering.png)

A small Ljung–Box p-value rejects 'RV is white noise' — the signature of volatility clustering. Jump share is max(RV − BV, 0)/RV summed over bars: bipower variation is jump-robust, so the excess of RV over BV estimates the discontinuous part. With one quiet overnight session, treat both as descriptive, not structural.