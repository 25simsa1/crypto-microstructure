# Cross-asset lead-lag

_Data: 2026-06-10 05:03 → 08:19 UTC (~3.3 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| pair | contemporaneous corr | peak lag | peak corr | 95% null band |
|---|---|---|---|---|
| BTCUSDT/ETHUSDT | +0.349 | +0s | +0.349 | 0.021 |
| BTCUSDT/SOLUSDT | +0.390 | +0s | +0.390 | 0.021 |
| ETHUSDT/SOLUSDT | +0.386 | +0s | +0.386 | 0.021 |

![chart](analysis_leadlag.png)

**Caveats:** 1 s last-observation sampling induces spurious lead-lag (Epps effect / asynchronous trading): the less active symbol's mid updates later, which *looks* like following. A peak at ±1 s within the null band is noise, not alpha. Single venue — cross-venue latency arbitrage is invisible here.