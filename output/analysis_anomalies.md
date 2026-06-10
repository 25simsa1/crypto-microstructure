# Anomaly episodes

_Data: 2026-06-10 05:03 → 08:52 UTC (~3.8 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Detectors use trailing median + MAD only (no future data). Spread spikes: >4x the trailing 15-min median for 3s+. Depth evaporation: <15% of trailing median within ±10 bps for 3s+. Vol shifts: 1-min RV >6 MADs over 30 min.

| symbol | kind | start (UTC) | duration | peak | baseline |
|---|---|---|---|---|---|
| BTCUSDT | vol_shift | 06:21:00 | 0s | 9.09e-07 | 1.76e-07 |
| ETHUSDT | spread_spike | 05:11:42 | 3s | 10.7 | 2.15 |
| ETHUSDT | spread_spike | 05:15:27 | 16s | 14.1 | 2.16 |
| ETHUSDT | spread_spike | 05:18:22 | 9s | 12 | 2.28 |
| ETHUSDT | spread_spike | 05:20:23 | 4s | 10 | 2.34 |
| ETHUSDT | spread_spike | 06:40:36 | 3s | 12.8 | 2.7 |
| ETHUSDT | depth_evaporation | 07:00:19 | 6s | 8.11e+03 | 5.91e+04 |
| ETHUSDT | spread_spike | 07:17:18 | 6s | 13 | 2.57 |
| ETHUSDT | vol_shift | 07:34:00 | 0s | 4e-06 | 5.17e-07 |
| ETHUSDT | vol_shift | 08:32:00 | 0s | 3.01e-06 | 6.14e-07 |
| ETHUSDT | spread_spike | 08:39:56 | 4s | 12.5 | 2.27 |
| ETHUSDT | spread_spike | 08:47:02 | 3s | 15.7 | 2.52 |
| SOLUSDT | vol_shift | 07:11:00 | 0s | 4.22e-06 | 6.24e-07 |

**13 episode(s) detected.**

![chart](analysis_anomalies.png)