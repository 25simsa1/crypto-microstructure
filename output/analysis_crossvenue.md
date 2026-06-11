# Cross-venue analysis: Kraken vs Coinbase

Capture cadence is ~1 snapshot/s/venue: **sub-second lead-lag is not measurable here** — lags below are in whole seconds. Stale book runs (content frozen >=120 s, e.g. the live Coinbase/ETH freeze caught by the quality layer) are excluded throughout.

## Lead-lag (full capture)

| symbol | contemporaneous corr | peak lag | peak corr | leader |
|---|---|---|---|---|
| BTC-USD | +0.587 | +0s | +0.587 | tie |
| ETH-USD | +0.639 | +0s | +0.639 | tie |
| SOL-USD | +0.667 | +0s | +0.667 | tie |

## Liquidity (median quoted spread, bps)

| symbol | kraken | coinbase |
|---|---|---|
| BTC-USD | 0.02 | 0.00 |
| ETH-USD | 0.06 | 0.06 |
| SOL-USD | 1.54 | 1.54 |

## Cross-venue mid divergence vs round-trip fees

| symbol | median (bps) | p99 | p99.9 | max |
|---|---|---|---|---|
| BTC-USD | 0.9 | 4.4 | 9.9 | 28.7 |
| ETH-USD | 0.8 | 4.7 | 13.7 | 26.4 |
| SOL-USD | 0.8 | 4.6 | 11.5 | 25.4 |

| fee scenario | round trip (bps) | seconds exceeding | share |
|---|---|---|---|
| taker+taker (Kraken 0.25%) | 145 | 0 | 0.0000% |
| taker+taker (Kraken 0.50%) | 170 | 0 | 0.0000% |
| maker+maker (CB 0.60% + Kraken 0.25%) | 85 | 0 | 0.0000% |

![chart](analysis_crossvenue.png)

**Maker caveat (registered fee answer):** the maker+maker line assumes both passive fills actually happen. Passive orders fill preferentially when price moves through them (adverse selection), so divergence > maker fees is *not* an executable profit — it is an upper bound on opportunity that ignores fill risk, queue position, and inventory/transfer latency between venues.

**Sensitivity:** the taker conclusion is identical at Kraken 0.25% and 0.50% — the binding cost is Coinbase's 1.20% taker.