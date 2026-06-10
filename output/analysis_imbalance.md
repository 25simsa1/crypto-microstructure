# Book pressure vs short-horizon returns

_Data: 2026-06-10 05:03 → 06:28 UTC (~1.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. **27 hypotheses tested → Bonferroni threshold |t| > 3.58** (plain |t|>1.96 would be cherry-picking).

| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |
|---|---|---|---|---|---|---|
| BTCUSDT | imb5 | 5s | -0.66 | +0.080 | 47.9% | 1,196 |
| BTCUSDT | imb5 | 30s | -1.34 | +0.196 | 49.4% | 1,196 |
| BTCUSDT | imb5 | 60s | -0.70 | +0.123 | 50.4% | 1,196 |
| BTCUSDT | ofi10 | 5s | -0.31 | -0.010 | 51.3% | 1,196 |
| BTCUSDT | ofi10 | 30s | -0.41 | -0.022 | 45.5% | 1,196 |
| BTCUSDT | ofi10 | 60s | -1.20 | -0.063 | 44.4% | 1,196 |
| BTCUSDT | mprem | 5s | -4.41 | -0.110 | 52.4% | 1,196 |
| BTCUSDT | mprem | 30s | -2.03 | -0.008 | 51.8% | 1,196 |
| BTCUSDT | mprem | 60s | -0.91 | -0.014 | 47.7% | 1,196 |
| ETHUSDT | imb5 | 5s | +2.17 | +0.066 | 46.6% | 1,037 |
| ETHUSDT | imb5 | 30s | +2.67 | +0.124 | 48.1% | 1,037 |
| ETHUSDT | imb5 | 60s | +2.32 | +0.088 | 51.3% | 1,037 |
| ETHUSDT | ofi10 | 5s | -0.22 | -0.062 | 49.5% | 1,037 |
| ETHUSDT | ofi10 | 30s | -0.91 | -0.047 | 49.3% | 1,037 |
| ETHUSDT | ofi10 | 60s | -1.83 | -0.058 | 48.7% | 1,037 |
| ETHUSDT | mprem | 5s | -3.86 | -0.182 | 52.4% | 1,037 |
| ETHUSDT | mprem | 30s | -1.43 | -0.078 | 52.0% | 1,037 |
| ETHUSDT | mprem | 60s | -0.59 | -0.040 | 46.8% | 1,037 |
| SOLUSDT | imb5 | 5s | -0.71 | +0.024 | 49.7% | 701 |
| SOLUSDT | imb5 | 30s | -1.72 | -0.155 | 44.2% | 701 |
| SOLUSDT | imb5 | 60s | -2.06 | -0.160 | 43.1% | 701 |
| SOLUSDT | ofi10 | 5s | +0.32 | -0.058 | 49.7% | 701 |
| SOLUSDT | ofi10 | 30s | -0.36 | +0.020 | 50.5% | 701 |
| SOLUSDT | ofi10 | 60s | +0.74 | -0.048 | 47.0% | 701 |
| SOLUSDT | mprem | 5s | -1.25 | -0.019 | 52.2% | 701 |
| SOLUSDT | mprem | 30s | +0.73 | -0.091 | 45.2% | 701 |
| SOLUSDT | mprem | 60s | +0.38 | -0.016 | 50.5% | 701 |

![chart](analysis_imbalance.png)

**Read honestly:** a significant train t-stat with near-zero OOS correlation means the relationship did not survive the regime change between the two parts of the night. Only combos clearing the Bonferroni bar *and* showing same-signed OOS correlation deserve attention, and even those are one-night, one-venue results.