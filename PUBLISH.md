# PUBLISH.md — eyeball checklist before flipping the repo public

The repo is currently **private** at `origin` (github.com/25simsa1/
crypto-microstructure). This session prepared but did **not** flip
visibility. Work through this list personally before doing so.

## Verified clean by the night-two scrub (re-verify if paranoid)

- [x] `data/` has **never** been tracked (`git log --stat -- data/` is
  empty) — raw capture stays local.
- [x] `watchdog_status.json` never tracked; in `.gitignore`.
- [x] No API keys, tokens, or auth anywhere (the loggers use public
  endpoints only; `git grep -iE 'api[_-]?key|token|secret'` to re-check).
- [x] No absolute `/Users/...` paths in tracked files (scripts use
  `Path(__file__)`-relative paths throughout).
- [x] `LICENSE` (MIT) added.

## Things the scrub found that are PUSHED IN HISTORY — eyeball and decide

1. **Your name and account appear in prose**, not just commit metadata:
   `NIGHT_LOG.md` ("ACTION FOR SIMON", "questions that need Simon") and
   older `MORNING.md` revisions (mention of the `25simsa1` account and
   GitHub plans). Commit author is `Simon Sang <simonlapsang@gmail.com>`.
   For a personal portfolio repo this is presumably fine — but it is
   *in pushed history*, so scrubbing would require a history rewrite +
   force push. Decide: acceptable (recommended) or rewrite before public.
2. **Fee tier details**: REPLICATION-answer fees ("Coinbase spot Intro 1
   = 1.20%/0.60%") describe your account's fee tier in
   `analysis_crossvenue.py` and FINDINGS. Mild personal-account info;
   eyeball whether you care.
3. **Capture timestamps reveal your sleep/wake schedule** (the quality
   report attributes gaps to "machine asleep"). Harmless but personal;
   your call.

## Before flipping public

- [ ] `make all && make check` green on a fresh clone (no local-only state).
- [ ] Read `FINDINGS.md` top to bottom once as a stranger would.
- [ ] Confirm `REPLICATION.md` and the results section agree on what was
  frozen vs post-hoc (the post-hoc staleness sensitivity must stay
  clearly labeled as not registered).
- [ ] Skim `git log` once for any commit message you would not want public.
- [ ] Decide on history item 1 above; if rewriting, do it BEFORE adding
  any collaborators or forks exist.
- [ ] Push the night-two commits (`git push origin main`), then flip
  visibility in GitHub settings.

## Deliberately NOT published

- Raw capture (`data/`) — local only; the parquet store and `output/`
  artifacts regenerate from it via `make all`, and `output/*.png` are
  gitignored (the markdown reports are tracked, charts regenerate).
