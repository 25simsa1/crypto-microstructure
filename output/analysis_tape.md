# Trade-tape analysis

_Data: 2026-06-10 05:03 → 08:19 UTC (~3.3 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | trades | buy share | median eff spread (bps) | median quoted (bps) | sign ACF lags 1-5 | LB p (10 lags) | runs z | volume bars |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 276 | 53% | 2.38 | 2.48 | -0.027 | 0.002 | +2.13 | 78 |
| ETHUSDT | 260 | 53% | 2.40 | 2.50 | +0.026 | 0.022 | +2.18 | 100 |
| SOLUSDT | 227 | 52% | 3.10 | 3.12 | +0.162 | 0.000 | -1.90 | 81 |

Pooled corr(net flow, bar return) across symbols: **+0.04**.

![chart](analysis_tape.png)

**Significance:** Ljung–Box (10 lags) tests 'signs are white noise'; the runs test z is negative under persistence. Both are joint with the thin-tape caveat below — a p of 0.04 on one night and one venue is a hint, not a finding.

**Caveats:** the overnight tape is thin (hundreds of trades, not thousands), so sign-ACF confidence bands are wide and the flow/return scatter is descriptive only. Effective spread uses the 1 s book mid as the benchmark — staleness up to 1 s biases it upward when the market moves between snapshot and trade.