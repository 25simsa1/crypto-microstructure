# Book pressure vs short-horizon returns

_Data: 2026-06-10 05:03 → 11:17 UTC (~6.2 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. **27 hypotheses tested → Bonferroni threshold |t| > 3.58** (plain |t|>1.96 would be cherry-picking).

| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |
|---|---|---|---|---|---|---|
| BTCUSDT | imb5 | 5s | +2.00 | +0.019 | 50.1% | 4,031 |
| BTCUSDT | imb5 | 30s | +1.16 | +0.015 | 49.8% | 4,031 |
| BTCUSDT | imb5 | 60s | -0.00 | +0.015 | 48.7% | 4,031 |
| BTCUSDT | ofi10 | 5s | -0.19 | +0.080 | 52.7% | 4,031 |
| BTCUSDT | ofi10 | 30s | -0.01 | +0.048 | 56.3% | 4,031 |
| BTCUSDT | ofi10 | 60s | -0.00 | +0.052 | 55.7% | 4,031 |
| BTCUSDT | mprem | 5s | -6.63 | +0.008 | 51.2% | 4,031 |
| BTCUSDT | mprem | 30s | -3.66 | -0.003 | 51.1% | 4,031 |
| BTCUSDT | mprem | 60s | -2.80 | +0.030 | 53.6% | 4,031 |
| ETHUSDT | imb5 | 5s | +1.29 | +0.003 | 50.8% | 4,252 |
| ETHUSDT | imb5 | 30s | +0.31 | -0.050 | 48.4% | 4,252 |
| ETHUSDT | imb5 | 60s | -0.14 | -0.051 | 48.3% | 4,252 |
| ETHUSDT | ofi10 | 5s | +0.70 | +0.009 | 50.1% | 4,252 |
| ETHUSDT | ofi10 | 30s | +0.76 | +0.035 | 51.5% | 4,252 |
| ETHUSDT | ofi10 | 60s | +0.60 | +0.041 | 51.2% | 4,252 |
| ETHUSDT | mprem | 5s | -8.63 | -0.066 | 49.3% | 4,252 |
| ETHUSDT | mprem | 30s | -3.60 | -0.029 | 52.4% | 4,252 |
| ETHUSDT | mprem | 60s | -2.50 | +0.024 | 53.8% | 4,252 |
| SOLUSDT | imb5 | 5s | +1.01 | +0.083 | 51.7% | 2,851 |
| SOLUSDT | imb5 | 30s | -1.83 | +0.045 | 52.2% | 2,851 |
| SOLUSDT | imb5 | 60s | -1.43 | +0.037 | 52.4% | 2,851 |
| SOLUSDT | ofi10 | 5s | +0.53 | +0.028 | 52.1% | 2,851 |
| SOLUSDT | ofi10 | 30s | -0.28 | +0.096 | 54.7% | 2,851 |
| SOLUSDT | ofi10 | 60s | +0.22 | +0.039 | 54.4% | 2,851 |
| SOLUSDT | mprem | 5s | -1.11 | -0.067 | 51.1% | 2,851 |
| SOLUSDT | mprem | 30s | -0.82 | -0.048 | 52.0% | 2,851 |
| SOLUSDT | mprem | 60s | -1.07 | -0.052 | 51.7% | 2,851 |

![chart](analysis_imbalance.png)

**Read honestly:** a significant train t-stat with near-zero OOS correlation means the relationship did not survive the regime change between the two parts of the night. Only combos clearing the Bonferroni bar *and* showing same-signed OOS correlation deserve attention, and even those are one-night, one-venue results.