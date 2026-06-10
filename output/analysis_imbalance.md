# Book pressure vs short-horizon returns

_Data: 2026-06-10 05:03 → 09:25 UTC (~4.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. **27 hypotheses tested → Bonferroni threshold |t| > 3.58** (plain |t|>1.96 would be cherry-picking).

| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |
|---|---|---|---|---|---|---|
| BTCUSDT | imb5 | 5s | +2.13 | +0.044 | 51.2% | 3,213 |
| BTCUSDT | imb5 | 30s | +1.43 | +0.013 | 52.2% | 3,213 |
| BTCUSDT | imb5 | 60s | +0.34 | +0.000 | 53.6% | 3,213 |
| BTCUSDT | ofi10 | 5s | -0.09 | -0.013 | 50.9% | 3,213 |
| BTCUSDT | ofi10 | 30s | -0.20 | -0.050 | 52.0% | 3,213 |
| BTCUSDT | ofi10 | 60s | -0.22 | -0.081 | 50.1% | 3,213 |
| BTCUSDT | mprem | 5s | -6.12 | -0.044 | 49.7% | 3,213 |
| BTCUSDT | mprem | 30s | -2.85 | -0.020 | 50.4% | 3,213 |
| BTCUSDT | mprem | 60s | -1.41 | -0.016 | 49.4% | 3,213 |
| ETHUSDT | imb5 | 5s | +2.27 | +0.002 | 52.1% | 3,297 |
| ETHUSDT | imb5 | 30s | +2.27 | -0.048 | 49.8% | 3,297 |
| ETHUSDT | imb5 | 60s | +1.70 | -0.052 | 51.5% | 3,297 |
| ETHUSDT | ofi10 | 5s | +1.16 | +0.000 | 49.3% | 3,297 |
| ETHUSDT | ofi10 | 30s | +0.77 | +0.038 | 50.0% | 3,297 |
| ETHUSDT | ofi10 | 60s | +0.59 | +0.038 | 48.6% | 3,297 |
| ETHUSDT | mprem | 5s | -8.64 | -0.047 | 47.3% | 3,297 |
| ETHUSDT | mprem | 30s | -3.37 | -0.043 | 46.7% | 3,297 |
| ETHUSDT | mprem | 60s | -2.40 | +0.002 | 45.9% | 3,297 |
| SOLUSDT | imb5 | 5s | +0.35 | +0.079 | 51.5% | 2,286 |
| SOLUSDT | imb5 | 30s | -2.42 | +0.062 | 49.4% | 2,286 |
| SOLUSDT | imb5 | 60s | -1.69 | +0.049 | 50.5% | 2,286 |
| SOLUSDT | ofi10 | 5s | +0.71 | -0.017 | 47.9% | 2,286 |
| SOLUSDT | ofi10 | 30s | -0.30 | +0.048 | 54.7% | 2,286 |
| SOLUSDT | ofi10 | 60s | +0.23 | +0.026 | 54.6% | 2,286 |
| SOLUSDT | mprem | 5s | -2.23 | +0.038 | 51.7% | 2,286 |
| SOLUSDT | mprem | 30s | -1.76 | +0.024 | 52.5% | 2,286 |
| SOLUSDT | mprem | 60s | -1.21 | -0.050 | 49.4% | 2,286 |

![chart](analysis_imbalance.png)

**Read honestly:** a significant train t-stat with near-zero OOS correlation means the relationship did not survive the regime change between the two parts of the night. Only combos clearing the Bonferroni bar *and* showing same-signed OOS correlation deserve attention, and even those are one-night, one-venue results.