# Cross-asset lead-lag

_Data: 2026-06-10 05:03 → 07:52 UTC (~2.8 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| pair | contemporaneous corr | peak lag | peak corr | 95% null band |
|---|---|---|---|---|
| BTCUSDT/ETHUSDT | +0.357 | +0s | +0.357 | 0.023 |
| BTCUSDT/SOLUSDT | +0.398 | +0s | +0.398 | 0.023 |
| ETHUSDT/SOLUSDT | +0.391 | +0s | +0.391 | 0.023 |

![chart](analysis_leadlag.png)

**Caveats:** 1 s last-observation sampling induces spurious lead-lag (Epps effect / asynchronous trading): the less active symbol's mid updates later, which *looks* like following. A peak at ±1 s within the null band is noise, not alpha. Single venue — cross-venue latency arbitrage is invisible here.