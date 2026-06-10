# Book pressure vs short-horizon returns

_Data: 2026-06-10 05:03 → 08:19 UTC (~3.3 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. **27 hypotheses tested → Bonferroni threshold |t| > 3.58** (plain |t|>1.96 would be cherry-picking).

| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |
|---|---|---|---|---|---|---|
| BTCUSDT | imb5 | 5s | +1.98 | +0.042 | 52.9% | 2,318 |
| BTCUSDT | imb5 | 30s | +0.93 | +0.059 | 51.9% | 2,318 |
| BTCUSDT | imb5 | 60s | +0.40 | +0.018 | 51.9% | 2,318 |
| BTCUSDT | ofi10 | 5s | -0.59 | +0.047 | 51.0% | 2,318 |
| BTCUSDT | ofi10 | 30s | -0.12 | -0.015 | 49.5% | 2,318 |
| BTCUSDT | ofi10 | 60s | -0.13 | -0.014 | 50.3% | 2,318 |
| BTCUSDT | mprem | 5s | -6.76 | -0.062 | 50.8% | 2,318 |
| BTCUSDT | mprem | 30s | -2.83 | -0.016 | 52.3% | 2,318 |
| BTCUSDT | mprem | 60s | -1.51 | -0.011 | 54.3% | 2,318 |
| ETHUSDT | imb5 | 5s | +2.64 | +0.027 | 51.4% | 2,260 |
| ETHUSDT | imb5 | 30s | +2.52 | +0.019 | 52.0% | 2,260 |
| ETHUSDT | imb5 | 60s | +2.46 | -0.016 | 52.5% | 2,260 |
| ETHUSDT | ofi10 | 5s | -0.82 | +0.091 | 53.1% | 2,260 |
| ETHUSDT | ofi10 | 30s | +0.14 | +0.098 | 50.7% | 2,260 |
| ETHUSDT | ofi10 | 60s | -0.66 | +0.116 | 53.6% | 2,260 |
| ETHUSDT | mprem | 5s | -8.14 | -0.084 | 51.4% | 2,260 |
| ETHUSDT | mprem | 30s | -4.24 | -0.025 | 54.0% | 2,260 |
| ETHUSDT | mprem | 60s | -2.47 | -0.049 | 52.1% | 2,260 |
| SOLUSDT | imb5 | 5s | +1.01 | -0.043 | 50.0% | 1,575 |
| SOLUSDT | imb5 | 30s | -1.47 | -0.152 | 46.9% | 1,575 |
| SOLUSDT | imb5 | 60s | -1.14 | -0.113 | 50.8% | 1,575 |
| SOLUSDT | ofi10 | 5s | +0.05 | +0.043 | 53.8% | 1,575 |
| SOLUSDT | ofi10 | 30s | -0.02 | -0.032 | 47.4% | 1,575 |
| SOLUSDT | ofi10 | 60s | +0.03 | +0.002 | 48.1% | 1,575 |
| SOLUSDT | mprem | 5s | -1.13 | -0.088 | 49.5% | 1,575 |
| SOLUSDT | mprem | 30s | -1.50 | -0.077 | 47.0% | 1,575 |
| SOLUSDT | mprem | 60s | -0.18 | -0.110 | 45.8% | 1,575 |

![chart](analysis_imbalance.png)

**Read honestly:** a significant train t-stat with near-zero OOS correlation means the relationship did not survive the regime change between the two parts of the night. Only combos clearing the Bonferroni bar *and* showing same-signed OOS correlation deserve attention, and even those are one-night, one-venue results.