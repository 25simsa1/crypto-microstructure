# Book pressure vs short-horizon returns

_Data: 2026-06-10 05:03 → 05:25 UTC (~0.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. **27 hypotheses tested → Bonferroni threshold |t| > 3.58** (plain |t|>1.96 would be cherry-picking).

| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |
|---|---|---|---|---|---|---|
| BTCUSDT | imb5 | 5s | -1.90 | -0.050 | 54.5% | 301 |
| BTCUSDT | imb5 | 30s | -2.74 | -0.023 | 52.8% | 301 |
| BTCUSDT | imb5 | 60s | -2.09 | -0.139 | 35.5% | 301 |
| BTCUSDT | ofi10 | 5s | -0.87 | -0.178 | 54.2% | 301 |
| BTCUSDT | ofi10 | 30s | -0.55 | -0.158 | 42.5% | 301 |
| BTCUSDT | ofi10 | 60s | -1.10 | -0.018 | 48.5% | 301 |
| BTCUSDT | mprem | 5s | -1.75 | -0.253 | 39.0% | 301 |
| BTCUSDT | mprem | 30s | -1.95 | -0.091 | 58.1% | 301 |
| BTCUSDT | mprem | 60s | -1.16 | -0.236 | 58.1% | 301 |
| ETHUSDT | imb5 | 5s | +0.54 | -0.018 | 47.0% | 309 |
| ETHUSDT | imb5 | 30s | +1.59 | -0.100 | 41.6% | 309 |
| ETHUSDT | imb5 | 60s | +1.86 | -0.218 | 29.1% | 309 |
| ETHUSDT | ofi10 | 5s | -1.06 | +0.036 | 50.7% | 309 |
| ETHUSDT | ofi10 | 30s | -1.86 | +0.046 | 47.1% | 309 |
| ETHUSDT | ofi10 | 60s | -1.76 | -0.134 | 46.6% | 309 |
| ETHUSDT | mprem | 5s | -1.74 | -0.062 | 55.9% | 309 |
| ETHUSDT | mprem | 30s | -0.97 | -0.019 | 55.2% | 309 |
| ETHUSDT | mprem | 60s | -1.48 | -0.119 | 56.6% | 309 |
| SOLUSDT | imb5 | 5s | +1.05 | +0.063 | 38.6% | 215 |
| SOLUSDT | imb5 | 30s | -0.27 | -0.020 | 41.9% | 215 |
| SOLUSDT | imb5 | 60s | -0.26 | -0.033 | 38.2% | 215 |
| SOLUSDT | ofi10 | 5s | -1.35 | +0.018 | 54.2% | 215 |
| SOLUSDT | ofi10 | 30s | -0.80 | -0.270 | 38.4% | 215 |
| SOLUSDT | ofi10 | 60s | -0.75 | -0.242 | 41.2% | 215 |
| SOLUSDT | mprem | 5s | -0.61 | +0.152 | 59.0% | 215 |
| SOLUSDT | mprem | 30s | -0.07 | +0.025 | 63.1% | 215 |
| SOLUSDT | mprem | 60s | -0.50 | +0.090 | 63.7% | 215 |

![chart](analysis_imbalance.png)

**Read honestly:** a significant train t-stat with near-zero OOS correlation means the relationship did not survive the regime change between the two parts of the night. Only combos clearing the Bonferroni bar *and* showing same-signed OOS correlation deserve attention, and even those are one-night, one-venue results.