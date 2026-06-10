# Cross-asset lead-lag

_Data: 2026-06-10 05:03 → 09:58 UTC (~4.9 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| pair | contemporaneous corr | peak lag | peak corr | 95% null band |
|---|---|---|---|---|
| BTCUSDT/ETHUSDT | +0.343 | +0s | +0.343 | 0.017 |
| BTCUSDT/SOLUSDT | +0.379 | +0s | +0.379 | 0.017 |
| ETHUSDT/SOLUSDT | +0.387 | +0s | +0.387 | 0.017 |

![chart](analysis_leadlag.png)

**Caveats:** 1 s last-observation sampling induces spurious lead-lag (Epps effect / asynchronous trading): the less active symbol's mid updates later, which *looks* like following. A peak at ±1 s within the null band is noise, not alpha. Single venue — cross-venue latency arbitrage is invisible here.