# Book pressure vs short-horizon returns

_Data: 2026-06-10 05:03 → 09:58 UTC (~4.9 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. **27 hypotheses tested → Bonferroni threshold |t| > 3.58** (plain |t|>1.96 would be cherry-picking).

| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |
|---|---|---|---|---|---|---|
| BTCUSDT | imb5 | 5s | +1.78 | +0.036 | 51.0% | 3,629 |
| BTCUSDT | imb5 | 30s | +1.42 | +0.012 | 51.3% | 3,629 |
| BTCUSDT | imb5 | 60s | +0.41 | +0.014 | 52.2% | 3,629 |
| BTCUSDT | ofi10 | 5s | -0.18 | +0.078 | 52.8% | 3,629 |
| BTCUSDT | ofi10 | 30s | -0.11 | +0.021 | 53.0% | 3,629 |
| BTCUSDT | ofi10 | 60s | -0.02 | +0.025 | 51.7% | 3,629 |
| BTCUSDT | mprem | 5s | -7.62 | +0.006 | 50.1% | 3,629 |
| BTCUSDT | mprem | 30s | -3.42 | -0.014 | 49.8% | 3,629 |
| BTCUSDT | mprem | 60s | -2.29 | +0.002 | 51.2% | 3,629 |
| ETHUSDT | imb5 | 5s | +1.51 | -0.011 | 50.6% | 3,795 |
| ETHUSDT | imb5 | 30s | +0.70 | -0.064 | 47.2% | 3,795 |
| ETHUSDT | imb5 | 60s | -0.14 | -0.044 | 48.2% | 3,795 |
| ETHUSDT | ofi10 | 5s | +1.11 | +0.001 | 49.8% | 3,795 |
| ETHUSDT | ofi10 | 30s | +1.14 | -0.031 | 48.5% | 3,795 |
| ETHUSDT | ofi10 | 60s | +0.81 | +0.013 | 48.3% | 3,795 |
| ETHUSDT | mprem | 5s | -8.77 | -0.056 | 49.3% | 3,795 |
| ETHUSDT | mprem | 30s | -3.64 | -0.032 | 50.9% | 3,795 |
| ETHUSDT | mprem | 60s | -2.73 | +0.034 | 53.2% | 3,795 |
| SOLUSDT | imb5 | 5s | +1.00 | +0.066 | 52.1% | 2,597 |
| SOLUSDT | imb5 | 30s | -1.67 | -0.002 | 49.3% | 2,597 |
| SOLUSDT | imb5 | 60s | -1.38 | -0.017 | 50.6% | 2,597 |
| SOLUSDT | ofi10 | 5s | +0.30 | +0.019 | 51.4% | 2,597 |
| SOLUSDT | ofi10 | 30s | +0.09 | +0.028 | 53.4% | 2,597 |
| SOLUSDT | ofi10 | 60s | +0.46 | +0.008 | 54.1% | 2,597 |
| SOLUSDT | mprem | 5s | -0.92 | -0.060 | 50.0% | 2,597 |
| SOLUSDT | mprem | 30s | -0.97 | -0.031 | 52.8% | 2,597 |
| SOLUSDT | mprem | 60s | -1.20 | -0.046 | 52.5% | 2,597 |

![chart](analysis_imbalance.png)

**Read honestly:** a significant train t-stat with near-zero OOS correlation means the relationship did not survive the regime change between the two parts of the night. Only combos clearing the Bonferroni bar *and* showing same-signed OOS correlation deserve attention, and even those are one-night, one-venue results.