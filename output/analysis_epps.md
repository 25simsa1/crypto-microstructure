# Epps effect

_Data: 2026-06-10 05:03 → 06:28 UTC (~1.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| pair | corr @ 1s | corr @ 300s | interval reaching half of 300s corr |
|---|---|---|---|
| BTCUSDT/ETHUSDT | +0.335 | +0.940 | 2s |
| BTCUSDT/SOLUSDT | +0.399 | +0.825 | 2s |
| ETHUSDT/SOLUSDT | +0.372 | +0.859 | 2s |

Observations per interval: 4,128 at 1s down to 17 at 300s.

![chart](analysis_epps.png)

**Read:** correlation rising with the sampling interval is the classic Epps signature of asynchronous price updates. The saturation timescale bounds how fast cross-asset information propagates *on this venue*. The 300 s points rest on few observations overnight — widest error bars on the right.