# Epps effect

_Data: 2026-06-10 05:03 → 08:52 UTC (~3.8 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| pair | corr @ 1s | corr @ 300s | interval reaching half of 300s corr |
|---|---|---|---|
| BTCUSDT/ETHUSDT | +0.341 | +0.942 | 2s |
| BTCUSDT/SOLUSDT | +0.374 | +0.873 | 2s |
| ETHUSDT/SOLUSDT | +0.384 | +0.870 | 2s |

Observations per interval: 10,878 at 1s down to 46 at 300s.

![chart](analysis_epps.png)

**Read:** correlation rising with the sampling interval is the classic Epps signature of asynchronous price updates. The saturation timescale bounds how fast cross-asset information propagates *on this venue*. The 300 s points rest on few observations overnight — widest error bars on the right.