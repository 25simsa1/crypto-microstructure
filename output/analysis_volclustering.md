# Volatility clustering and jumps

_Data: 2026-06-10 05:03 → 07:24 UTC (~2.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | mean ACF lags 1-5 | Ljung-Box p (10 lags) | median ann. vol | jump share of variance |
|---|---|---|---|---|
| BTCUSDT | +0.282 | 1.3e-15 | 35.8% | 32.8% |
| ETHUSDT | +0.108 | 0.035 | 60.2% | 21.0% |
| SOLUSDT | +0.046 | 0.048 | 65.0% | 33.1% |

![chart](analysis_volclustering.png)

A small Ljung–Box p-value rejects 'RV is white noise' — the signature of volatility clustering. Jump share is max(RV − BV, 0)/RV summed over bars: bipower variation is jump-robust, so the excess of RV over BV estimates the discontinuous part. With one quiet overnight session, treat both as descriptive, not structural.