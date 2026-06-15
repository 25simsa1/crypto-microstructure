# H1 replication — SOL trade-sign order-flow memory

_Generated 2026-06-15 03:53 UTC by `scripts/replication_h1.py`. Frozen procedure from REPLICATION.md; side convention from SIDE_CONVENTION.md (kraken as-is, coinbase negated)._

Benchmark — night one (Binance.US): ACF(1-5)=+0.15, LB p<0.001, runs z=-2.8, n=364.

Primary hypothesis is **SOL**. BTC/ETH are descriptive context (night one showed bid-ask-bounce alternation there, not the hypothesis).

| venue | symbol | window | ACF(1-5) | LB p (10 lags) | runs z | n | verdict |
|---|---|---|---|---|---|---|---|
| kraken | BTC-USD | matched | +0.3662 | 0.00e+00 | -57.76 | 10,758 | (descriptive) |
| kraken | BTC-USD | full | +0.4034 | 0.00e+00 | -179.98 | 88,844 | (descriptive) |
| kraken | ETH-USD | matched | +0.3168 | 0.00e+00 | -45.83 | 6,273 | (descriptive) |
| kraken | ETH-USD | full | +0.3452 | 0.00e+00 | -125.49 | 45,076 | (descriptive) |
| kraken | SOL-USD | matched | +0.2606 | 0.00e+00 | -27.27 | 4,299 | REPLICATED |
| kraken | SOL-USD | full | +0.3417 | 0.00e+00 | -91.93 | 34,195 | REPLICATED |
| coinbase | BTC-USD | matched | +0.3635 | 0.00e+00 | -168.23 | 85,241 | (descriptive) |
| coinbase | BTC-USD | full | +0.3561 | 0.00e+00 | -421.63 | 663,939 | (descriptive) |
| coinbase | ETH-USD | matched | +0.4500 | 0.00e+00 | -136.67 | 41,284 | (descriptive) |
| coinbase | ETH-USD | full | +0.4587 | 0.00e+00 | -338.37 | 257,040 | (descriptive) |
| coinbase | SOL-USD | matched | +0.3347 | 0.00e+00 | -79.12 | 20,852 | REPLICATED |
| coinbase | SOL-USD | full | +0.4002 | 0.00e+00 | -227.37 | 149,028 | REPLICATED |

## POST-HOC fragmentation sensitivity (not registered)

A taker order sweeping several levels prints as multiple same-side trades (often one timestamp), which mechanically inflates sign persistence. Collapsing each same-timestamp run to one net-signed event (full capture):

| venue | symbol | same-ts share | raw ACF(1-5) | collapsed ACF(1-5) | n raw | n collapsed |
|---|---|---|---|---|---|---|
| kraken | SOL-USD | 34.7% | +0.342 | +0.159 | 34,203 | 22,336 |
| coinbase | SOL-USD | 30.5% | +0.400 | +0.291 | 149,044 | 103,641 |

Both venues retain ACF(1-5) well above the +0.05 replication bar after collapsing; Kraken lands at ~+0.16, essentially night one's +0.15. The replication is robust to fragmentation, not an artifact of it.

## Verdict (primary hypothesis, SOL, matched-hours window)

- **kraken**: REPLICATED
- **coinbase**: REPLICATED

## Reading

Cross-venue replication (registered): night one was Binance.US; this is Kraken + Coinbase. Both venues replicating = the SOL order-flow-memory regularity is venue-robust, a strictly stronger claim than night one alone. A split or failure is reported as-is — a failed pre-registered replication is itself a finding.

The side convention is load-bearing: Coinbase's `side` had to be negated (empirically, 11% raw agreement with the quote-derived aggressor vs Kraken's 98.6% control). Had it been used raw, Coinbase's ACF sign would invert — the exact silent error the side-convention step existed to prevent.
