# Book pressure vs short-horizon returns

_Data: 2026-06-10 05:03 → 05:58 UTC (~0.9 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. **27 hypotheses tested → Bonferroni threshold |t| > 3.58** (plain |t|>1.96 would be cherry-picking).

| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |
|---|---|---|---|---|---|---|
| BTCUSDT | imb5 | 5s | -1.13 | +0.010 | 45.9% | 766 |
| BTCUSDT | imb5 | 30s | -1.29 | -0.037 | 40.6% | 766 |
| BTCUSDT | imb5 | 60s | -0.77 | +0.024 | 42.4% | 766 |
| BTCUSDT | ofi10 | 5s | -0.50 | +0.059 | 50.5% | 766 |
| BTCUSDT | ofi10 | 30s | -0.72 | +0.087 | 53.8% | 766 |
| BTCUSDT | ofi10 | 60s | -1.26 | -0.038 | 48.6% | 766 |
| BTCUSDT | mprem | 5s | -3.98 | -0.131 | 47.2% | 766 |
| BTCUSDT | mprem | 30s | -1.83 | -0.095 | 48.8% | 766 |
| BTCUSDT | mprem | 60s | -1.17 | +0.059 | 54.8% | 766 |
| ETHUSDT | imb5 | 5s | +1.34 | +0.083 | 47.8% | 680 |
| ETHUSDT | imb5 | 30s | +1.86 | +0.175 | 51.7% | 680 |
| ETHUSDT | imb5 | 60s | +1.45 | +0.162 | 48.7% | 680 |
| ETHUSDT | ofi10 | 5s | -0.43 | +0.052 | 50.5% | 680 |
| ETHUSDT | ofi10 | 30s | -0.87 | -0.062 | 45.7% | 680 |
| ETHUSDT | ofi10 | 60s | -1.60 | -0.121 | 43.1% | 680 |
| ETHUSDT | mprem | 5s | -2.91 | -0.129 | 55.8% | 680 |
| ETHUSDT | mprem | 30s | -1.34 | -0.003 | 55.2% | 680 |
| ETHUSDT | mprem | 60s | -1.24 | +0.088 | 55.4% | 680 |
| SOLUSDT | imb5 | 5s | -0.58 | -0.077 | 43.2% | 458 |
| SOLUSDT | imb5 | 30s | -1.08 | -0.238 | 41.9% | 458 |
| SOLUSDT | imb5 | 60s | -1.51 | -0.230 | 39.9% | 458 |
| SOLUSDT | ofi10 | 5s | +0.39 | +0.014 | 49.7% | 458 |
| SOLUSDT | ofi10 | 30s | -0.06 | +0.003 | 53.3% | 458 |
| SOLUSDT | ofi10 | 60s | +0.63 | +0.047 | 54.7% | 458 |
| SOLUSDT | mprem | 5s | -1.43 | -0.002 | 49.1% | 458 |
| SOLUSDT | mprem | 30s | +0.12 | +0.055 | 56.8% | 458 |
| SOLUSDT | mprem | 60s | -0.63 | +0.104 | 61.6% | 458 |

![chart](analysis_imbalance.png)

**Read honestly:** a significant train t-stat with near-zero OOS correlation means the relationship did not survive the regime change between the two parts of the night. Only combos clearing the Bonferroni bar *and* showing same-signed OOS correlation deserve attention, and even those are one-night, one-venue results.