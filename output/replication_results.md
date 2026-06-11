# Replication results (pre-registered: see REPLICATION.md)

Matched window: 2026-06-11 08:03 → 13:34 UTC. H1 (trade-sign memory) is NOT TESTABLE on this capture (book-only); registered as a capture-design finding.

## kraken

| symbol | window coverage | void? |
|---|---|---|
| BTC-USD | 80.1% | ok |
| ETH-USD | 80.1% | ok |
| SOL-USD | 80.1% | ok |

| H2 tick-sign | window | ACF(1-5) | LB p | n ticks | night-1 bench | verdict |
|---|---|---|---|---|---|---|
| SOL-USD | matched | -0.0115 | 1.12e-03 | 4,205 | -0.0143 | not significant |
| SOL-USD | full-day | -0.0054 | 8.10e-14 | 33,204 | -0.0143 | descriptive (robustness) |
| ETH-USD | matched | +0.0231 | 7.35e-10 | 6,169 | -0.0172 | SIGN FLIP |
| ETH-USD | full-day | +0.0244 | 3.83e-59 | 45,440 | -0.0172 | descriptive (robustness) |
| BTC-USD | matched | +0.0819 | 3.33e-28 | 1,809 | +0.0005 | descriptive |
| BTC-USD | full-day | +0.0559 | 2.63e-128 | 28,272 | +0.0005 | descriptive |

**H3 Epps (BTC/ETH, matched window):** corr +0.415 @ 1s → +0.889 @ 300s (rise +0.474; night-1: +0.345 → +0.928). **REPLICATED**

## coinbase

| symbol | window coverage | void? |
|---|---|---|
| BTC-USD | 78.7% | ok |
| ETH-USD | 78.7% | ok |
| SOL-USD | 78.7% | ok |

| H2 tick-sign | window | ACF(1-5) | LB p | n ticks | night-1 bench | verdict |
|---|---|---|---|---|---|---|
| SOL-USD | matched | -0.0044 | 5.51e-02 | 2,305 | -0.0143 | not significant |
| SOL-USD | full-day | +0.0036 | 6.67e-06 | 28,571 | -0.0143 | descriptive (robustness) |
| ETH-USD | matched | +0.0318 | 1.90e-07 | 5,832 | -0.0172 | SIGN FLIP |
| ETH-USD | full-day | +0.0281 | 4.82e-76 | 43,975 | -0.0172 | descriptive (robustness) |
| BTC-USD | matched | +0.0691 | 1.04e-67 | 6,013 | +0.0005 | descriptive |
| BTC-USD | full-day | +0.0573 | 0.00e+00 | 45,560 | +0.0005 | descriptive |

**H3 Epps (BTC/ETH, matched window):** corr +0.698 @ 1s → +0.854 @ 300s (rise +0.156; night-1: +0.345 → +0.928). **FAILED**

## Verdict summary (matched window, per registration)

- **kraken**: SOL not significant, ETH SIGN FLIP, Epps REPLICATED
- **coinbase**: SOL not significant, ETH SIGN FLIP, Epps FAILED
## POST-HOC sensitivity: stale-book exclusion (not registered)

Frozen-book episodes were discovered after the registered run (see venue_quality.md). Same frozen procedure, stale runs (>=120 s unchanged top-of-book with snapshots arriving) excluded:

| venue | symbol | fresh coverage | ACF(1-5) | LB p | n ticks | registered verdict | sensitivity verdict |
|---|---|---|---|---|---|---|---|
| kraken | SOL-USD | 80.1% | -0.0115 | 1.12e-03 | 4,205 | not significant | not significant |
| kraken | ETH-USD | 80.1% | +0.0231 | 7.35e-10 | 6,169 | SIGN FLIP | SIGN FLIP |
| coinbase | SOL-USD | 59.7% | -0.0044 | 5.51e-02 | 2,305 | not significant | VOID (fresh coverage < 70%) |
| coinbase | ETH-USD | 61.0% | +0.0318 | 1.90e-07 | 5,832 | SIGN FLIP | VOID (fresh coverage < 70%) |

Stale runs emit zero mid ticks, so they dilute n rather than fabricate signs; agreement between the two columns means the registered verdicts were not artifacts of staleness.

![epps](replication_epps.png)

_Cross-venue caveat (registered): pass = venue-robust regularity; fail = ambiguous between night-one noise and venue heterogeneity._