# Volatility clustering and jumps

_Data: 2026-06-10 05:03 → 10:33 UTC (~5.5 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | mean ACF lags 1-5 | Ljung-Box p (10 lags) | median ann. vol | jump share of variance |
|---|---|---|---|---|
| BTCUSDT | +0.216 | 1.2e-25 | 42.9% | 30.4% |
| ETHUSDT | +0.145 | 5.1e-08 | 60.5% | 21.5% |
| SOLUSDT | +0.077 | 0.00084 | 66.5% | 32.2% |

![chart](analysis_volclustering.png)

A small Ljung–Box p-value rejects 'RV is white noise' — the signature of volatility clustering. Jump share is max(RV − BV, 0)/RV summed over bars: bipower variation is jump-robust, so the excess of RV over BV estimates the discontinuous part. With one quiet overnight session, treat both as descriptive, not structural.