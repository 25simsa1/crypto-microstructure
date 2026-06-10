# Trade-tape analysis

_Data: 2026-06-10 05:03 → 07:24 UTC (~2.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | trades | buy share | median eff spread (bps) | median quoted (bps) | sign ACF lags 1-5 | volume bars |
|---|---|---|---|---|---|---|
| BTCUSDT | 211 | 57% | 2.34 | 2.43 | -0.052 | 65 |
| ETHUSDT | 184 | 55% | 2.48 | 2.58 | +0.006 | 77 |
| SOLUSDT | 170 | 55% | 3.11 | 3.12 | +0.165 | 70 |

Pooled corr(net flow, bar return) across symbols: **+0.06**.

![chart](analysis_tape.png)

**Caveats:** the overnight tape is thin (hundreds of trades, not thousands), so sign-ACF confidence bands are wide and the flow/return scatter is descriptive only. Effective spread uses the 1 s book mid as the benchmark — staleness up to 1 s biases it upward when the market moves between snapshot and trade.