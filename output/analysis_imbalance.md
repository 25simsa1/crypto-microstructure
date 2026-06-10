# Book pressure vs short-horizon returns

_Data: 2026-06-10 05:03 → 07:24 UTC (~2.4 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. **27 hypotheses tested → Bonferroni threshold |t| > 3.58** (plain |t|>1.96 would be cherry-picking).

| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |
|---|---|---|---|---|---|---|
| BTCUSDT | imb5 | 5s | +0.85 | +0.053 | 52.9% | 1,765 |
| BTCUSDT | imb5 | 30s | +0.48 | +0.066 | 54.2% | 1,765 |
| BTCUSDT | imb5 | 60s | +0.25 | +0.089 | 53.5% | 1,765 |
| BTCUSDT | ofi10 | 5s | -0.17 | -0.071 | 48.9% | 1,765 |
| BTCUSDT | ofi10 | 30s | -0.29 | +0.006 | 46.7% | 1,765 |
| BTCUSDT | ofi10 | 60s | -1.35 | +0.198 | 51.2% | 1,765 |
| BTCUSDT | mprem | 5s | -5.15 | -0.137 | 47.7% | 1,765 |
| BTCUSDT | mprem | 30s | -2.04 | -0.053 | 48.5% | 1,765 |
| BTCUSDT | mprem | 60s | -1.14 | -0.023 | 51.2% | 1,765 |
| ETHUSDT | imb5 | 5s | +2.86 | +0.019 | 49.6% | 1,640 |
| ETHUSDT | imb5 | 30s | +3.57 | -0.035 | 46.6% | 1,640 |
| ETHUSDT | imb5 | 60s | +2.82 | +0.021 | 46.6% | 1,640 |
| ETHUSDT | ofi10 | 5s | -0.94 | -0.009 | 52.6% | 1,640 |
| ETHUSDT | ofi10 | 30s | -0.78 | +0.006 | 54.6% | 1,640 |
| ETHUSDT | ofi10 | 60s | -1.29 | -0.021 | 53.8% | 1,640 |
| ETHUSDT | mprem | 5s | -6.53 | -0.205 | 49.7% | 1,640 |
| ETHUSDT | mprem | 30s | -2.85 | -0.122 | 49.8% | 1,640 |
| ETHUSDT | mprem | 60s | -1.48 | -0.096 | 50.6% | 1,640 |
| SOLUSDT | imb5 | 5s | -0.46 | +0.112 | 54.0% | 1,149 |
| SOLUSDT | imb5 | 30s | -1.99 | -0.024 | 48.6% | 1,149 |
| SOLUSDT | imb5 | 60s | -2.09 | +0.017 | 46.8% | 1,149 |
| SOLUSDT | ofi10 | 5s | -0.43 | +0.011 | 52.1% | 1,149 |
| SOLUSDT | ofi10 | 30s | +0.01 | -0.045 | 46.1% | 1,149 |
| SOLUSDT | ofi10 | 60s | +0.68 | -0.101 | 47.2% | 1,149 |
| SOLUSDT | mprem | 5s | -0.78 | -0.022 | 50.1% | 1,149 |
| SOLUSDT | mprem | 30s | -0.23 | -0.090 | 46.0% | 1,149 |
| SOLUSDT | mprem | 60s | -0.29 | +0.016 | 49.0% | 1,149 |

![chart](analysis_imbalance.png)

**Read honestly:** a significant train t-stat with near-zero OOS correlation means the relationship did not survive the regime change between the two parts of the night. Only combos clearing the Bonferroni bar *and* showing same-signed OOS correlation deserve attention, and even those are one-night, one-venue results.