# Trade-tape analysis

_Data: 2026-06-10 05:03 → 06:55 UTC (~1.9 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | trades | buy share | median eff spread (bps) | median quoted (bps) | sign ACF lags 1-5 | volume bars |
|---|---|---|---|---|---|---|
| BTCUSDT | 161 | 56% | 2.26 | 2.35 | -0.050 | 51 |
| ETHUSDT | 139 | 53% | 2.45 | 2.58 | +0.001 | 50 |
| SOLUSDT | 137 | 54% | 1.57 | 3.12 | +0.206 | 58 |

Pooled corr(net flow, bar return) across symbols: **+0.12**.

![chart](analysis_tape.png)

**Caveats:** the overnight tape is thin (hundreds of trades, not thousands), so sign-ACF confidence bands are wide and the flow/return scatter is descriptive only. Effective spread uses the 1 s book mid as the benchmark — staleness up to 1 s biases it upward when the market moves between snapshot and trade.