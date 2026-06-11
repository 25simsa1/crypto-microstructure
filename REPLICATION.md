# REPLICATION.md — pre-registered night-two replication plan

**Status: FROZEN at registration time (2026-06-11, before any night-two
statistic was computed). Per CLAUDE.md this file is never edited after
registration. Results go in FINDINGS.md / NIGHT_LOG.md, not here.**

## Disclosure of prior contact with night-two data

Before this registration, night-two files were touched only to (a) read
three sample lines per venue to learn the JSON schema, and (b) count
`type` values (`grep -o '"type":"..."' | uniq -c`) to check whether a
trade channel exists. No prices were aggregated, no statistic was
computed. The night-one benchmark numbers below were computed on
night-one (Binance.US) data only.

## Context and an honest constraint discovered at design time

Night one (2026-06-10, Binance.US, 08:03–13:34 UTC) found, as its
headline result: **SOL trade-sign order-flow memory** — mean trade-sign
ACF over lags 1–5 ≈ **+0.15**, Ljung–Box (10 lags) **p < 0.001**, runs
z ≈ **−2.8**, stable from ~200 to 364 trades.

**The night-two capture (Kraken + Coinbase) is book-only — the venue
loggers subscribe to no trade channel.** The primary hypothesis is
therefore *untestable on this dataset*. That is recorded as a finding
about capture design (H1 verdict: NOT TESTABLE), not silently replaced.
Any future trade-channel capture can test H1 against this registration.

## H1 (primary, registered for the record): SOL trade-sign memory

- Procedure (frozen, verbatim from night one): trade signs = sign of
  `signed_qty` (+1 buy-aggressor, −1 sell); mean of pandas
  `Series.autocorr(lag=k)` for k = 1..5; Ljung–Box at 10 lags on the
  sign series; Wald–Wolfowitz runs z.
- Replication = LB p < 0.001 AND mean ACF(1–5) ≥ +0.05 (same sign as
  night one). Partial = 0.001 ≤ p < 0.05 with positive ACF. Failure =
  insignificant or sign-flipped.
- **Verdict on night-two data: NOT TESTABLE (no trade events captured).**

## H2 (secondary analogue, frozen before any night-two computation):
## mid-price tick-direction memory

The closest book-only analogue. It is **not** the same phenomenon as
H1: on night one itself, trade signs persisted (+0.15) while mid-tick
directions *anti*-persisted. H2 therefore tests whether the night-one
**anti-persistence of mid ticks** generalizes across venues.

- Procedure (frozen): per venue and symbol — mid = (best bid + best
  ask)/2 from each book snapshot, resampled to a 1 s grid by last
  observation; first differences; drop zeros; signs; statistic 1 =
  mean ACF lags 1–5; statistic 2 = Ljung–Box p at 10 lags.
- Night-one benchmark (Binance.US, full capture, computed 2026-06-11
  before this registration, code identical to the frozen procedure):
  - SOL: ACF(1–5) = **−0.0143**, LB p = 3.8e-13, n = 9,501 ticks
  - BTC: ACF(1–5) = **+0.0005**, LB p = 3.8e-14, n = 11,817
  - ETH: ACF(1–5) = **−0.0172**, LB p = 1.7e-18, n = 14,893
- **Replication criterion (per venue, matched window):** SOL and ETH
  each show ACF(1–5) < 0 with LB p < 0.001. **Full replication** = both
  venues pass. **Partial** = exactly one venue passes. **Failure** =
  neither, or a significant *positive* ACF(1–5) (sign flip).
- BTC is registered as descriptive only (night-one value ≈ 0 supports
  no directional prediction).

## H3: Epps curve re-test (BTC/ETH)

- Procedure (frozen, verbatim from night one's `analysis_epps.py`):
  Pearson correlation of log mid returns of BTC-USD vs ETH-USD on
  last-observation grids at sampling intervals 1, 2, 5, 10, 30, 60,
  120, 300 s; no interpolation across gaps.
- Night-one benchmark: corr = 0.345 @ 1 s rising to 0.928 @ 300 s.
- **Replication criterion (per venue, matched window):**
  corr(300 s) − corr(1 s) ≥ +0.30 AND corr(300 s) ≥ 0.70.

## Windows, venues, and multiplicity (frozen)

1. **Matched overnight window first:** 08:03–13:34 UTC on 2026-06-11
   (night one's exact capture hours, next day). Verdicts above are
   defined on this window.
2. **Full-day window second**, reported separately as descriptive
   robustness (day regime did not exist on night one; no verdict
   hinges on it).
3. Venues analyzed separately (Kraken, Coinbase); no pooling.
4. Test count: H2 = 2 symbols × 2 venues, H3 = 2 venues. The LB p <
   0.001 threshold was chosen at night-one strength; with 6 verdict
   tests, the implied family-wise error at α = 0.001 per test is
   ≤ 0.6% — no further correction applied, and this is frozen.

## Cross-venue honesty note (as instructed)

Night one was Binance.US; night two is Kraken + Coinbase. This is a
**cross-venue replication**: if it passes, the regularity is venue-
robust — a strictly stronger claim than same-venue stability. If it
fails, the result is **ambiguous** between (a) the night-one finding
being noise and (b) genuine venue heterogeneity; the writeup must say
so and may not pick (b) without independent evidence.

## What would make this exercise void

Coverage < 70% in the matched window for a venue (per the Phase-2
quality report) voids that venue's verdict rather than counting as
failure; the report must state which verdicts were voided and why.
