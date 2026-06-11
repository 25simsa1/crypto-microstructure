# Venue capture quality (Kraken vs Coinbase)

| venue | symbol | snapshots | span (h) | coverage | cadence med/p95 (s) | crossed | locked | backwards ts |
|---|---|---|---|---|---|---|---|---|
| coinbase | BTC-USD | 74,404 | 30.2 | 71.51% | 1.02 / 1.12 | 0 | 0 | 0 |
| coinbase | ETH-USD | 74,404 | 30.2 | 71.51% | 1.02 / 1.12 | 0 | 0 | 0 |
| coinbase | SOL-USD | 74,403 | 30.2 | 71.51% | 1.02 / 1.12 | 0 | 0 | 0 |
| kraken | BTC-USD | 77,053 | 30.2 | 72.32% | 1.00 / 1.08 | 0 | 0 | 0 |
| kraken | ETH-USD | 77,053 | 30.2 | 72.32% | 1.00 / 1.08 | 0 | 0 | 0 |
| kraken | SOL-USD | 77,053 | 30.2 | 72.32% | 1.00 / 1.08 | 0 | 0 | 0 |

## Gaps (heartbeat-attributed)

| attribution | count | total s | longest |
|---|---|---|---|
| feed-outage | 21 | 9,249 | 1,018s (coinbase/BTC-USD @ 06-10 22:50:25) |
| logger-down | 360 | 144,180 | 1,157s (kraken/BTC-USD @ 06-11 02:24:18) |
| symbol-quiet | 84 | 10,893 | 1,039s (coinbase/BTC-USD @ 06-11 01:03:18) |
| unattributed-short | 1111 | 18,858 | 82s (coinbase/BTC-USD @ 06-11 00:12:55) |

`feed-outage` = logger heartbeating but disconnected/not writing; `logger-down` = no heartbeats inside a >=90s gap (process not running, e.g. machine asleep); `symbol-quiet` = logger alive and writing, this symbol silent; `unattributed-short` = gap too short for heartbeat evidence either way.