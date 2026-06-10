# Questions for Simon — answer over coffee ☕

Decisions I made unilaterally overnight are marked (decided); override any of them.

1. **Audience for the final write-up?** "Impress hedge funds" — is this a portfolio
   piece (GitHub repo + README + research note, polished for recruiters/quant funds),
   or groundwork for an actual strategy? Changes whether I optimize for presentation
   or for signal research. *(decided meanwhile: writing RESEARCH.md as a desk-style
   research note, repo-ready)*

2. **Publish as a GitHub repo?** I can structure it (src/, notebooks/, README with
   figures) but won't create/push a repo without your say-so.

3. **Symbol set:** stuck with BTC/ETH/SOL on Binance.US. Want more (DOGE, XRP, ADA)
   or fewer-but-deeper? More symbols = more cross-sectional claims in the write-up.

4. **Cross-venue data (decided: yes):** I'm adding Coinbase + Kraken top-of-book
   polling so the note can include venue lead-lag / price discovery — the single most
   hedge-fund-flavored analysis available with free data. Veto if you object.

5. **Disk budget:** overnight total should land well under 200 MB in data/. If you
   want multi-night collection (much stronger seasonality claims), say so and I'll
   make the loggers a launchd service.
