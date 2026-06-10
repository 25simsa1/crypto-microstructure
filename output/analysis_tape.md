# Trade-tape analysis

_Data: 2026-06-10 05:03 → 09:58 UTC (~4.9 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

| symbol | trades | buy share | median eff spread (bps) | median quoted (bps) | sign ACF lags 1-5 | LB p (10 lags) | runs z | volume bars |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 408 | 51% | 2.41 | 2.52 | +0.029 | 0.003 | +1.30 | 120 |
| ETHUSDT | 391 | 50% | 2.34 | 2.50 | +0.053 | 0.009 | +1.06 | 141 |
| SOLUSDT | 333 | 50% | 3.11 | 3.14 | +0.178 | 0.000 | -3.90 | 117 |

Pooled corr(net flow, bar return) across symbols: **+0.05**.

![chart](analysis_tape.png)

**Significance:** Ljung–Box (10 lags) tests 'signs are white noise'; the runs test z is negative under persistence. Both are joint with the thin-tape caveat below — a p of 0.04 on one night and one venue is a hint, not a finding.

**Caveats:** the overnight tape is thin (hundreds of trades, not thousands), so sign-ACF confidence bands are wide and the flow/return scatter is descriptive only. Effective spread uses the 1 s book mid as the benchmark — staleness up to 1 s biases it upward when the market moves between snapshot and trade.