# Cross-asset lead-lag

_Data: 2026-06-10 05:03 → 09:25 UTC (~4.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| pair | contemporaneous corr | peak lag | peak corr | 95% null band |
|---|---|---|---|---|
| BTCUSDT/ETHUSDT | +0.339 | +0s | +0.339 | 0.018 |
| BTCUSDT/SOLUSDT | +0.378 | +0s | +0.378 | 0.018 |
| ETHUSDT/SOLUSDT | +0.385 | +0s | +0.385 | 0.018 |

![chart](analysis_leadlag.png)

**Caveats:** 1 s last-observation sampling induces spurious lead-lag (Epps effect / asynchronous trading): the less active symbol's mid updates later, which *looks* like following. A peak at ±1 s within the null band is noise, not alpha. Single venue — cross-venue latency arbitrage is invisible here.