# Good morning ☕ — overnight report & questions

**TL;DR:** the loggers ran all night (99.3–99.9% coverage). On top of the
capture I built a full research platform — typed data layer → Parquet,
tested feature library, 7 statistical studies, an anti-lookahead
backtester — all in git with `make check` green (ruff + strict mypy +
34 tests). Read `FINDINGS.md` for results, `NIGHT_LOG.md` for the
play-by-play.

## The three results worth your attention

1. **SOL shows real order-flow memory** — trade-sign Ljung–Box p < 0.001,
   ACF(1–5) ≈ +0.15. BTC/ETH show the opposite (bid-ask bounce
   alternation). One night, one venue — but it's the only signal that
   survived a significance test. (BTC later produced one Bonferroni-clearing
   t-stat — microprice premium at 5 s — but wrong-signed vs theory and
   OOS-weak: bid-ask-bounce mean reversion, not signal.)
2. **Textbook Epps effect** — BTC/ETH return correlation is 0.34 at 1 s
   sampling and 0.94 at 5 min. Cross-asset information takes ~minutes to
   fully propagate on this venue; this is also why naive 1 s lead-lag
   finds nothing.
3. **Everything loses money, provably** — the imbalance strategy family's
   best config has deflated Sharpe 0.00 and sits inside the random-null
   distribution. Fees (20 bps round trip) vs spreads (~2 bps) make
   taker-only HFT structurally unprofitable here. The writeup says so.

## Decisions I made overnight (override any)

- Kept BTC/ETH/SOL only; skipped the cross-venue Coinbase/Kraken poller
  (would have meant a third logger process mid-night; clean single-venue
  story instead, caveats documented).
- Retracted an early "SOL trades print at half the quoted spread"
  finding when it died on a thicker tape — it's in NIGHT_LOG as an
  example of small-sample honesty.

## Questions for you

1. **Stop or continue the capture?** The loggers keep running until you
   `pkill -f logger.py`. A second night would let the seasonality study
   make real time-of-day claims. (Multi-night = I'd set up launchd.)
2. **Publish?** This is GitHub-ready (README, architecture diagram,
   FINDINGS). Want me to create a repo under 25simsa1 and push? And if
   so: public or private?
3. **Backtest fee tier:** I assumed 10 bps taker. If you have an actual
   Binance.US fee tier in mind (they run promos as low as 0), say so —
   it changes the backtest conclusion section, not the code.
4. **Next research direction, if any:** cross-venue price discovery
   (needs the Coinbase/Kraken poller), maker-side simulation (needs
   order-book deltas, a bigger logger change), or multi-night
   seasonality (just needs patience)?
