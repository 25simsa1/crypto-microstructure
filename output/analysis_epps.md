# Epps effect

_Data: 2026-06-10 05:03 → 09:25 UTC (~4.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| pair | corr @ 1s | corr @ 300s | interval reaching half of 300s corr |
|---|---|---|---|
| BTCUSDT/ETHUSDT | +0.339 | +0.939 | 2s |
| BTCUSDT/SOLUSDT | +0.377 | +0.844 | 2s |
| ETHUSDT/SOLUSDT | +0.385 | +0.836 | 2s |

Observations per interval: 12,576 at 1s down to 53 at 300s.

![chart](analysis_epps.png)

**Read:** correlation rising with the sampling interval is the classic Epps signature of asynchronous price updates. The saturation timescale bounds how fast cross-asset information propagates *on this venue*. The 300 s points rest on few observations overnight — widest error bars on the right.