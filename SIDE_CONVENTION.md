# SIDE_CONVENTION.md — empirically determined trade-side semantics

_Generated 2026-06-12 20:52 UTC by `scripts/validate_trade_side.py` from on-disk capture only._

Method: Lee–Ready quote rule against the same venue's book capture (quote at-or-before the trade's exchange ts, max age 2.0s; trades strictly inside the spread are unclassifiable at 1 s cadence and excluded — their share is reported, not guessed).

## kraken

| symbol | trades | joined | classifiable | inside-spread | agreement (side == aggressor) |
|---|---|---|---|---|---|
| BTC-USD | 824 | 824 | 812 | 1.5% | 98.9% (803/812) |
| ETH-USD | 414 | 414 | 397 | 4.1% | 98.7% (392/397) |
| SOL-USD | 250 | 249 | 247 | 0.8% | 96.8% (239/247) |

**Pooled agreement: 98.49% over 1,456 classifiable trades.**

**Verdict: side = AGGRESSOR (taker) — use as-is**

Quote-age sensitivity (agreement should not degrade much with age if the join is sound; sharp degradation would mean stale quotes are driving misclassification):

| quote age | agreement | n |
|---|---|---|
| 0.0–0.5s | 99.9% | 700 |
| 0.5–1.0s | 97.2% | 748 |
| 1.0–2.0s | 100.0% | 8 |

Restricted to quotes ≤1 s old: 98.48% (1,448 trades).

Per-side symmetry (a true convention inverts/agrees on BOTH recorded sides; asymmetry would mean something subtler): recorded buy: 97.3% agreement over 704, recorded sell: 99.6% agreement over 752.

## coinbase

| symbol | trades | joined | classifiable | inside-spread | agreement (side == aggressor) |
|---|---|---|---|---|---|
| BTC-USD | 13,845 | 13,840 | 13,697 | 1.0% | 12.6% (1,722/13,697) |
| ETH-USD | 4,397 | 4,396 | 4,329 | 1.5% | 10.7% (464/4,329) |
| SOL-USD | 2,099 | 2,099 | 2,074 | 1.2% | 4.9% (102/2,074) |

**Pooled agreement: 11.38% over 20,100 classifiable trades.**

**Verdict: side = MAKER (resting) — NEGATE before use**

Quote-age sensitivity (agreement should not degrade much with age if the join is sound; sharp degradation would mean stale quotes are driving misclassification):

| quote age | agreement | n |
|---|---|---|
| 0.0–0.5s | 9.2% | 9,721 |
| 0.5–1.0s | 13.6% | 10,094 |
| 1.0–2.0s | 8.1% | 285 |

Restricted to quotes ≤1 s old: 11.43% (19,815 trades).

Per-side symmetry (a true convention inverts/agrees on BOTH recorded sides; asymmetry would mean something subtler): recorded buy: 12.4% agreement over 9,737, recorded sell: 10.4% agreement over 10,363.

## Instructions for the H1 re-run

- **kraken**: side = AGGRESSOR (taker) — use as-is
- **coinbase**: side = MAKER (resting) — NEGATE before use

## Confidence and limitations

- Book cadence is 1 s: the prevailing quote can be up to ~1 s stale (plus ~50-90 ms receive-vs-exchange skew), which both misclassifies some fast-market trades and leaves inside-spread trades unclassifiable. The age-bucket tables above quantify the effect; a stable agreement rate across buckets means staleness is not driving the verdict.
- Kraken is the control (documented taker convention): a high Kraken agreement validates the pipeline; the Coinbase verdict inherits that validation.
- What would raise confidence further: more hours of trades (larger n per symbol), and event-driven book capture (sub-second quotes) to shrink the unclassifiable share.
