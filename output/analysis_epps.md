# Epps effect

_Data: 2026-06-10 05:03 → 07:52 UTC (~2.8 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| pair | corr @ 1s | corr @ 300s | interval reaching half of 300s corr |
|---|---|---|---|
| BTCUSDT/ETHUSDT | +0.357 | +0.950 | 2s |
| BTCUSDT/SOLUSDT | +0.398 | +0.912 | 2s |
| ETHUSDT/SOLUSDT | +0.391 | +0.907 | 2s |

Observations per interval: 7,851 at 1s down to 34 at 300s.

![chart](analysis_epps.png)

**Read:** correlation rising with the sampling interval is the classic Epps signature of asynchronous price updates. The saturation timescale bounds how fast cross-asset information propagates *on this venue*. The 300 s points rest on few observations overnight — widest error bars on the right.