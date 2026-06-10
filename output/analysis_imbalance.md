# Book pressure vs short-horizon returns

_Data: 2026-06-10 05:03 → 08:52 UTC (~3.8 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. **27 hypotheses tested → Bonferroni threshold |t| > 3.58** (plain |t|>1.96 would be cherry-picking).

| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |
|---|---|---|---|---|---|---|
| BTCUSDT | imb5 | 5s | +1.47 | +0.047 | 51.3% | 2,777 |
| BTCUSDT | imb5 | 30s | +0.77 | +0.060 | 52.6% | 2,777 |
| BTCUSDT | imb5 | 60s | +0.33 | +0.010 | 54.1% | 2,777 |
| BTCUSDT | ofi10 | 5s | -0.51 | +0.017 | 52.3% | 2,777 |
| BTCUSDT | ofi10 | 30s | -0.16 | -0.004 | 51.2% | 2,777 |
| BTCUSDT | ofi10 | 60s | -0.12 | -0.025 | 50.3% | 2,777 |
| BTCUSDT | mprem | 5s | -6.27 | -0.072 | 50.0% | 2,777 |
| BTCUSDT | mprem | 30s | -2.34 | -0.054 | 48.3% | 2,777 |
| BTCUSDT | mprem | 60s | -0.96 | -0.063 | 47.5% | 2,777 |
| ETHUSDT | imb5 | 5s | +2.18 | -0.009 | 51.2% | 2,784 |
| ETHUSDT | imb5 | 30s | +2.21 | +0.002 | 55.1% | 2,784 |
| ETHUSDT | imb5 | 60s | +1.83 | -0.027 | 58.4% | 2,784 |
| ETHUSDT | ofi10 | 5s | +1.13 | +0.010 | 49.9% | 2,784 |
| ETHUSDT | ofi10 | 30s | +0.85 | +0.041 | 50.3% | 2,784 |
| ETHUSDT | ofi10 | 60s | +0.70 | +0.045 | 49.9% | 2,784 |
| ETHUSDT | mprem | 5s | -8.89 | -0.085 | 48.6% | 2,784 |
| ETHUSDT | mprem | 30s | -3.81 | -0.062 | 47.6% | 2,784 |
| ETHUSDT | mprem | 60s | -2.50 | -0.062 | 44.2% | 2,784 |
| SOLUSDT | imb5 | 5s | +0.83 | +0.017 | 48.3% | 1,962 |
| SOLUSDT | imb5 | 30s | -1.82 | -0.067 | 45.7% | 1,962 |
| SOLUSDT | imb5 | 60s | -1.18 | -0.091 | 49.1% | 1,962 |
| SOLUSDT | ofi10 | 5s | +0.14 | +0.022 | 51.8% | 1,962 |
| SOLUSDT | ofi10 | 30s | -0.74 | +0.044 | 53.6% | 1,962 |
| SOLUSDT | ofi10 | 60s | -0.41 | +0.073 | 52.7% | 1,962 |
| SOLUSDT | mprem | 5s | -1.33 | -0.009 | 50.3% | 1,962 |
| SOLUSDT | mprem | 30s | -1.66 | +0.019 | 51.7% | 1,962 |
| SOLUSDT | mprem | 60s | -0.39 | -0.063 | 48.0% | 1,962 |

![chart](analysis_imbalance.png)

**Read honestly:** a significant train t-stat with near-zero OOS correlation means the relationship did not survive the regime change between the two parts of the night. Only combos clearing the Bonferroni bar *and* showing same-signed OOS correlation deserve attention, and even those are one-night, one-venue results.