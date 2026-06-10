# Cross-asset lead-lag

_Data: 2026-06-10 05:03 → 08:52 UTC (~3.8 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| pair | contemporaneous corr | peak lag | peak corr | 95% null band |
|---|---|---|---|---|
| BTCUSDT/ETHUSDT | +0.341 | +0s | +0.341 | 0.019 |
| BTCUSDT/SOLUSDT | +0.374 | +0s | +0.374 | 0.019 |
| ETHUSDT/SOLUSDT | +0.384 | +0s | +0.384 | 0.019 |

![chart](analysis_leadlag.png)

**Caveats:** 1 s last-observation sampling induces spurious lead-lag (Epps effect / asynchronous trading): the less active symbol's mid updates later, which *looks* like following. A peak at ±1 s within the null band is noise, not alpha. Single venue — cross-venue latency arbitrage is invisible here.