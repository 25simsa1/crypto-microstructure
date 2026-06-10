# Cross-asset lead-lag

_Data: 2026-06-10 05:03 → 06:28 UTC (~1.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| pair | contemporaneous corr | peak lag | peak corr | 95% null band |
|---|---|---|---|---|
| BTCUSDT/ETHUSDT | +0.335 | +0s | +0.335 | 0.031 |
| BTCUSDT/SOLUSDT | +0.399 | +0s | +0.399 | 0.031 |
| ETHUSDT/SOLUSDT | +0.371 | +0s | +0.371 | 0.031 |

![chart](analysis_leadlag.png)

**Caveats:** 1 s last-observation sampling induces spurious lead-lag (Epps effect / asynchronous trading): the less active symbol's mid updates later, which *looks* like following. A peak at ±1 s within the null band is noise, not alpha. Single venue — cross-venue latency arbitrage is invisible here.