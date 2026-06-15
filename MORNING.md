# Status report — H1 replication landed ☕

## Headline: the pre-registered H1 test REPLICATED, cross-venue (2026-06-14)

SOL trade-sign order-flow memory — night one's headline — was re-run on
independent venues under the frozen `REPLICATION.md` procedure and
**replicated on both Kraken and Coinbase**:

| | SOL ACF(1–5), matched hours | Ljung–Box p | n |
|---|---|---|---|
| Kraken | +0.26 | ~0 | 4,299 |
| Coinbase | +0.33 | ~0 | 20,852 |
| _night one (Binance.US)_ | _+0.15_ | _<0.001_ | _364_ |

**What this is:** independent-data, cross-venue confirmation of a
*known* effect — order-flow sign autocorrelation (Cont et al.; Lillo–
Farmer long memory). The contribution is rigor and replication, **not a
new market law**. Three venues now agree.

**What keeps it honest (all in FINDINGS Part II):**
- **Print-fragmentation confound, caught in a bug hunt.** Raw ACF came
  back 2–3× night one and suspiciously uniform across every symbol. A
  taker order sweeping levels prints as many same-side trades (~30–35%
  share a timestamp), inflating sign persistence. Collapsing each
  same-timestamp run to one net event: Kraken falls to **+0.159 (≈ night
  one's +0.15)**, Coinbase to +0.291 — both still clear the +0.05 bar.
  Robust to the confound, not driven by it.
- **The side-convention validation was load-bearing.** Coinbase's `side`
  field is the *maker* side (11% raw agreement vs Kraken's 98.6% control,
  in `SIDE_CONVENTION.md`); used raw it would have inverted Coinbase's
  ACF sign and faked a failure. Catching that first is why this worked.
- 1 s book cadence, retail-venue data, single trade-channel feed per
  venue — same limitations as everything else here.

## This does NOT change the economic null

Separate finding, still stands: **no strategy in the tested family beats
fees.** Retail round-trip cost (~85–170 bps) is ~1000× the per-trade
edge; cross-venue mid divergence never once exceeded a round trip.
Order-flow memory being statistically real and being *tradable at retail*
are different claims — the first replicated, the second remains false.

## The night-two book-only verdicts stand as recorded (don't retcon)

The progression, dated and preserved in FINDINGS:
- **Night two (06-11), book-only:** H1 was **NOT TESTABLE** (no trade
  channel). The tick-sign *analogue* (H2) did not replicate; Epps (H3)
  replicated on Kraken, criterion-failed on Coinbase. That mixed verdict
  is real and stays.
- **06-12 onward:** trade channels added as separate loggers → H1 became
  testable → replicated (above). The earlier "mixed/inconclusive" was
  the honest answer *for book-only data*; H1 is the answer once trades
  exist.

## Logger status — healthy, survived two nights

All four loggers (2 book + 2 trade, Kraken + Coinbase) alive. The
indefinite-retry fix held: 41–47 reconnects each over the run, every one
recovered instead of exiting (the failure mode that ended the 06-11
capture). Last watchdog check: both venues green. Trade tape now ~55 h:
Kraken 34k / Coinbase 149k SOL trades, ~90–400× night one.

## Open options (your call)

1. **Refresh + publish prep.** Public docs now match FINDINGS; `PUBLISH.md`
   still has the eyeball checklist (name/account in pushed history; MIT
   LICENSE in place). Nothing pushed yet.
2. **Re-run H2** now that Coinbase isn't coverage-voided (the data-quality
   freeze that voided it is fixed).
3. **Keep capturing** — every day strengthens H1 and enables real
   multi-day seasonality.
