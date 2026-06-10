# Book pressure vs short-horizon returns

_Data: 2026-06-10 05:03 → 05:30 UTC (~0.5 h of single-venue Binance.US capture). Conclusions are conditional on this one overnight session._

Chronological 70/30 split. HAC (Newey–West) t-stats, lags = horizon. **27 hypotheses tested → Bonferroni threshold |t| > 3.58** (plain |t|>1.96 would be cherry-picking).

| symbol | feature | horizon | train t (HAC) | OOS corr | OOS hit rate | n test |
|---|---|---|---|---|---|---|
| BTCUSDT | imb5 | 5s | -2.59 | +0.061 | 43.0% | 386 |
| BTCUSDT | imb5 | 30s | -2.98 | +0.137 | 39.1% | 386 |
| BTCUSDT | imb5 | 60s | -2.63 | +0.079 | 29.3% | 386 |
| BTCUSDT | ofi10 | 5s | -0.88 | -0.171 | 52.2% | 386 |
| BTCUSDT | ofi10 | 30s | -1.52 | -0.001 | 56.7% | 386 |
| BTCUSDT | ofi10 | 60s | -1.06 | -0.227 | 55.2% | 386 |
| BTCUSDT | mprem | 5s | -2.92 | -0.125 | 45.8% | 386 |
| BTCUSDT | mprem | 30s | -2.16 | -0.060 | 45.6% | 386 |
| BTCUSDT | mprem | 60s | -1.77 | +0.075 | 53.9% | 386 |
| ETHUSDT | imb5 | 5s | +0.36 | -0.012 | 43.3% | 386 |
| ETHUSDT | imb5 | 30s | +0.85 | -0.049 | 37.6% | 386 |
| ETHUSDT | imb5 | 60s | +0.09 | -0.062 | 33.9% | 386 |
| ETHUSDT | ofi10 | 5s | -0.79 | -0.036 | 50.9% | 386 |
| ETHUSDT | ofi10 | 30s | -1.27 | -0.074 | 49.2% | 386 |
| ETHUSDT | ofi10 | 60s | -1.88 | -0.182 | 52.3% | 386 |
| ETHUSDT | mprem | 5s | -1.58 | -0.153 | 55.1% | 386 |
| ETHUSDT | mprem | 30s | -0.65 | -0.015 | 60.4% | 386 |
| ETHUSDT | mprem | 60s | -1.07 | -0.064 | 61.9% | 386 |
| SOLUSDT | imb5 | 5s | +1.08 | -0.223 | 34.6% | 281 |
| SOLUSDT | imb5 | 30s | -0.55 | -0.254 | 31.8% | 281 |
| SOLUSDT | imb5 | 60s | -0.66 | -0.290 | 28.7% | 281 |
| SOLUSDT | ofi10 | 5s | -0.94 | -0.031 | 48.9% | 281 |
| SOLUSDT | ofi10 | 30s | -1.73 | -0.192 | 43.6% | 281 |
| SOLUSDT | ofi10 | 60s | -0.87 | -0.098 | 52.1% | 281 |
| SOLUSDT | mprem | 5s | +0.01 | -0.143 | 52.7% | 281 |
| SOLUSDT | mprem | 30s | -0.17 | +0.015 | 70.1% | 281 |
| SOLUSDT | mprem | 60s | -0.39 | -0.139 | 70.9% | 281 |

![chart](analysis_imbalance.png)

**Read honestly:** a significant train t-stat with near-zero OOS correlation means the relationship did not survive the regime change between the two parts of the night. Only combos clearing the Bonferroni bar *and* showing same-signed OOS correlation deserve attention, and even those are one-night, one-venue results.