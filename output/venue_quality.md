# Venue capture quality (Kraken vs Coinbase)

| venue | symbol | snapshots | span (h) | coverage | cadence med/p95 (s) | crossed | locked | backwards ts |
|---|---|---|---|---|---|---|---|---|
| coinbase | BTC-USD | 74,901 | 30.3 | 71.64% | 1.02 / 1.12 | 0 | 0 | 0 |
| coinbase | ETH-USD | 74,901 | 30.3 | 71.65% | 1.02 / 1.12 | 0 | 0 | 0 |
| coinbase | SOL-USD | 74,900 | 30.3 | 71.64% | 1.02 / 1.12 | 0 | 0 | 0 |
| kraken | BTC-USD | 77,559 | 30.4 | 72.44% | 1.00 / 1.08 | 0 | 0 | 0 |
| kraken | ETH-USD | 77,559 | 30.4 | 72.44% | 1.00 / 1.08 | 0 | 0 | 0 |
| kraken | SOL-USD | 77,559 | 30.4 | 72.44% | 1.00 / 1.08 | 0 | 0 | 0 |

## Gaps (heartbeat-attributed)

| attribution | count | total s | longest |
|---|---|---|---|
| feed-outage | 21 | 9,249 | 1,018s (coinbase/BTC-USD @ 06-10 22:50:25) |
| logger-down | 360 | 144,180 | 1,157s (kraken/BTC-USD @ 06-11 02:24:18) |
| symbol-quiet | 84 | 10,893 | 1,039s (coinbase/BTC-USD @ 06-11 01:03:18) |
| unattributed-short | 1111 | 18,858 | 82s (coinbase/BTC-USD @ 06-11 00:12:55) |

`feed-outage` = logger heartbeating but disconnected/not writing; `logger-down` = no heartbeats inside a >=90s gap (process not running, e.g. machine asleep); `symbol-quiet` = logger alive and writing, this symbol silent; `unattributed-short` = gap too short for heartbeat evidence either way.
## Stale books (content frozen >=120s while snapshots arrive)

- **coinbase/ETH-USD**: 06-11 09:49:42 → 11:17:19 UTC (88 min)
- **coinbase/ETH-USD**: 06-11 17:09:00 → 18:47:22 UTC (98 min)
- **coinbase/SOL-USD**: 06-11 12:29:57 → 13:43:49 UTC (74 min)