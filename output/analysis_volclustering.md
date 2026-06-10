# Volatility clustering and jumps

_Data: 2026-06-10 05:03 → 07:52 UTC (~2.8 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | mean ACF lags 1-5 | Ljung-Box p (10 lags) | median ann. vol | jump share of variance |
|---|---|---|---|---|
| BTCUSDT | +0.227 | 1e-12 | 37.1% | 32.5% |
| ETHUSDT | +0.078 | 0.073 | 57.4% | 23.8% |
| SOLUSDT | +0.049 | 0.011 | 63.9% | 32.7% |

![chart](analysis_volclustering.png)

A small Ljung–Box p-value rejects 'RV is white noise' — the signature of volatility clustering. Jump share is max(RV − BV, 0)/RV summed over bars: bipower variation is jump-robust, so the excess of RV over BV estimates the discontinuous part. With one quiet overnight session, treat both as descriptive, not structural.