# Book pressure vs short-horizon returns

_Data: 2026-06-10 05:03 → 10:33 UTC (~5.5 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. **27 hypotheses tested → Bonferroni threshold |t| > 3.58** (plain |t|>1.96 would be cherry-picking).

| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |
|---|---|---|---|---|---|---|
| BTCUSDT | imb5 | 5s | +1.93 | +0.018 | 50.3% | 3,996 |
| BTCUSDT | imb5 | 30s | +1.21 | +0.013 | 50.0% | 3,996 |
| BTCUSDT | imb5 | 60s | +0.12 | +0.011 | 48.9% | 3,996 |
| BTCUSDT | ofi10 | 5s | -0.20 | +0.080 | 52.5% | 3,996 |
| BTCUSDT | ofi10 | 30s | -0.02 | +0.046 | 56.2% | 3,996 |
| BTCUSDT | ofi10 | 60s | -0.02 | +0.051 | 55.8% | 3,996 |
| BTCUSDT | mprem | 5s | -6.52 | +0.004 | 51.1% | 3,996 |
| BTCUSDT | mprem | 30s | -3.57 | -0.006 | 51.0% | 3,996 |
| BTCUSDT | mprem | 60s | -2.69 | +0.025 | 53.1% | 3,996 |
| ETHUSDT | imb5 | 5s | +1.42 | -0.001 | 50.6% | 4,219 |
| ETHUSDT | imb5 | 30s | +0.34 | -0.052 | 48.4% | 4,219 |
| ETHUSDT | imb5 | 60s | -0.17 | -0.051 | 48.2% | 4,219 |
| ETHUSDT | ofi10 | 5s | +0.74 | +0.006 | 49.9% | 4,219 |
| ETHUSDT | ofi10 | 30s | +0.76 | +0.034 | 51.2% | 4,219 |
| ETHUSDT | ofi10 | 60s | +0.61 | +0.038 | 50.7% | 4,219 |
| ETHUSDT | mprem | 5s | -8.58 | -0.068 | 49.3% | 4,219 |
| ETHUSDT | mprem | 30s | -3.55 | -0.037 | 51.9% | 4,219 |
| ETHUSDT | mprem | 60s | -2.47 | +0.018 | 53.6% | 4,219 |
| SOLUSDT | imb5 | 5s | +1.06 | +0.077 | 51.4% | 2,840 |
| SOLUSDT | imb5 | 30s | -1.80 | +0.041 | 51.9% | 2,840 |
| SOLUSDT | imb5 | 60s | -1.42 | +0.035 | 52.2% | 2,840 |
| SOLUSDT | ofi10 | 5s | +0.47 | +0.029 | 51.9% | 2,840 |
| SOLUSDT | ofi10 | 30s | -0.25 | +0.090 | 54.5% | 2,840 |
| SOLUSDT | ofi10 | 60s | +0.28 | +0.032 | 54.2% | 2,840 |
| SOLUSDT | mprem | 5s | -1.05 | -0.068 | 51.1% | 2,840 |
| SOLUSDT | mprem | 30s | -0.81 | -0.047 | 52.0% | 2,840 |
| SOLUSDT | mprem | 60s | -1.05 | -0.052 | 51.8% | 2,840 |

![chart](analysis_imbalance.png)

**Read honestly:** a significant train t-stat with near-zero OOS correlation means the relationship did not survive the regime change between the two parts of the night. Only combos clearing the Bonferroni bar *and* showing same-signed OOS correlation deserve attention, and even those are one-night, one-venue results.