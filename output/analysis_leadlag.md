# Cross-asset lead-lag

_Data: 2026-06-10 05:03 → 05:30 UTC (~0.5 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| pair | contemporaneous corr | peak lag | peak corr | 95% null band |
|---|---|---|---|---|
| BTCUSDT/ETHUSDT | +0.303 | +0s | +0.303 | 0.053 |
| BTCUSDT/SOLUSDT | +0.346 | +0s | +0.346 | 0.053 |
| ETHUSDT/SOLUSDT | +0.347 | +0s | +0.347 | 0.053 |

![chart](analysis_leadlag.png)

**Caveats:** 1 s last-observation sampling induces spurious lead-lag (Epps effect / asynchronous trading): the less active symbol's mid updates later, which *looks* like following. A peak at ±1 s within the null band is noise, not alpha. Single venue — cross-venue latency arbitrage is invisible here.