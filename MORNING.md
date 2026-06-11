# Morning report — night two (Kraken + Coinbase) ☕

## ⚠️ Logger status — one needs your attention

- **Coinbase `venue_logger.py`: ETH book FROZEN since 17:09 UTC** (still
  writing snapshots and healthy heartbeats, but the ETH content never
  changes — per-symbol book-state corruption). BTC/SOL on Coinbase are
  fine. **It needs a restart**; this session was not allowed to touch
  it. Earlier freezes also hit ETH (88 min) and SOL (74 min) mid-day.
- Kraken logger: healthy.
- Both venues lost ~28% of the 30 h span to the machine sleeping
  (attributed explicitly in `output/venue_quality.md`). If you want
  clean multi-day capture: keep the lid open or `caffeinate` the
  venue loggers too.

## Replication verdict (pre-registered; full detail in FINDINGS Part II)

- **H1 — SOL trade-sign memory (the night-one headline): NOT TESTABLE.**
  The venue capture is book-only; no trade channel was subscribed. This
  is a capture-design finding — next capture should add trade streams.
- **H2 — tick-sign analogue: did not replicate.** SOL not significant
  on Kraken (misses the frozen p<0.001 bar at p=0.00112, same sign);
  ETH **sign-flipped** (significantly positive vs Binance.US's
  negative). Post-hoc staleness sensitivity: Kraken verdicts robust;
  **Coinbase verdicts VOID** (fresh coverage 60-61% < 70%).
- **H3 — Epps curve: REPLICATED on Kraken** (0.42 → 0.89); FAILED the
  frozen rise-criterion on Coinbase because its 1 s correlation already
  starts at 0.70 — effect present but much weaker there.
- Honest reading: night-one tick-sign dynamics look **venue-specific**
  (the two new venues agree with each other against Binance.US);
  Epps-style correlation build-up generalizes qualitatively.

## Cross-venue results (the dataset's unique capability)

- **No exploitable divergence:** Kraken-vs-Coinbase mid divergence
  median ~0.9 bps, p99 ~4.6 bps, max ~29 bps — **zero seconds** exceed
  a round trip at your fee levels (145–170 bps taker–taker; 85 bps
  maker–maker, with fill-risk caveats in the report). Insensitive to
  the Kraken 0.25–0.50% range; Coinbase's 1.20% taker is the binding
  cost.
- **No 1 s lead-lag** between venues (peak at lag 0 everywhere);
  sub-second leadership is not measurable at 1 snap/s — stated, not
  papered over.
- The catch of the day: a fabricated 286 bps ETH "divergence" traced to
  the frozen Coinbase book → new staleness detector in the quality
  layer (now part of `make data`).

## Publish prep (Phase 5) — waiting on you

`PUBLISH.md` has the eyeball checklist. Notably: your name/account
appear in pushed history (NIGHT_LOG/old MORNING revisions) — decide
"acceptable" vs history-rewrite before flipping public. LICENSE (MIT)
added. **Nothing was pushed this session**; `git push origin main` is
on the checklist.

## Next questions

1. Restart the Coinbase logger (and add trade-channel subscriptions so
   H1 becomes testable on a future capture)?
2. Push night-two commits and work through PUBLISH.md?
3. Keep capturing for multi-day seasonality, or stop the loggers?
