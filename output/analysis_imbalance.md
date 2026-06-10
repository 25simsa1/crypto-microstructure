# Book pressure vs short-horizon returns

_Data: 2026-06-10 05:03 → 07:52 UTC (~2.8 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. **27 hypotheses tested → Bonferroni threshold |t| > 3.58** (plain |t|>1.96 would be cherry-picking).

| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |
|---|---|---|---|---|---|---|
| BTCUSDT | imb5 | 5s | +1.51 | +0.028 | 52.5% | 1,988 |
| BTCUSDT | imb5 | 30s | +0.87 | +0.027 | 54.0% | 1,988 |
| BTCUSDT | imb5 | 60s | +0.52 | -0.004 | 53.0% | 1,988 |
| BTCUSDT | ofi10 | 5s | -0.55 | -0.001 | 48.5% | 1,988 |
| BTCUSDT | ofi10 | 30s | -0.19 | +0.013 | 49.1% | 1,988 |
| BTCUSDT | ofi10 | 60s | -0.29 | +0.068 | 49.4% | 1,988 |
| BTCUSDT | mprem | 5s | -5.49 | -0.093 | 49.0% | 1,988 |
| BTCUSDT | mprem | 30s | -1.90 | -0.038 | 50.2% | 1,988 |
| BTCUSDT | mprem | 60s | -0.93 | -0.019 | 53.0% | 1,988 |
| ETHUSDT | imb5 | 5s | +2.11 | +0.052 | 52.0% | 1,903 |
| ETHUSDT | imb5 | 30s | +2.56 | -0.012 | 50.1% | 1,903 |
| ETHUSDT | imb5 | 60s | +2.23 | -0.015 | 47.3% | 1,903 |
| ETHUSDT | ofi10 | 5s | -0.37 | +0.075 | 52.9% | 1,903 |
| ETHUSDT | ofi10 | 30s | +0.29 | +0.142 | 51.6% | 1,903 |
| ETHUSDT | ofi10 | 60s | -0.56 | +0.135 | 51.2% | 1,903 |
| ETHUSDT | mprem | 5s | -6.74 | -0.177 | 49.7% | 1,903 |
| ETHUSDT | mprem | 30s | -3.46 | -0.088 | 51.4% | 1,903 |
| ETHUSDT | mprem | 60s | -2.36 | -0.061 | 53.2% | 1,903 |
| SOLUSDT | imb5 | 5s | +0.59 | +0.049 | 54.7% | 1,287 |
| SOLUSDT | imb5 | 30s | -1.14 | -0.130 | 46.0% | 1,287 |
| SOLUSDT | imb5 | 60s | -0.89 | -0.096 | 45.8% | 1,287 |
| SOLUSDT | ofi10 | 5s | -0.05 | +0.012 | 50.9% | 1,287 |
| SOLUSDT | ofi10 | 30s | +0.33 | -0.067 | 45.4% | 1,287 |
| SOLUSDT | ofi10 | 60s | +1.08 | -0.133 | 42.5% | 1,287 |
| SOLUSDT | mprem | 5s | -1.68 | +0.020 | 50.8% | 1,287 |
| SOLUSDT | mprem | 30s | -1.31 | -0.058 | 46.7% | 1,287 |
| SOLUSDT | mprem | 60s | -0.38 | -0.038 | 49.5% | 1,287 |

![chart](analysis_imbalance.png)

**Read honestly:** a significant train t-stat with near-zero OOS correlation means the relationship did not survive the regime change between the two parts of the night. Only combos clearing the Bonferroni bar *and* showing same-signed OOS correlation deserve attention, and even those are one-night, one-venue results.