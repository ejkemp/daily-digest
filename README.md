# Daily Digest

A personal daily newsletter. Every morning a launchd job on the Mac Mini scrapes a set of
sources, has Claude (headless `claude -p`) write a digest, and publishes it as an Atom
feed via GitHub Pages.

**Sources:** Wikipedia Current Events · Hacker News (≥ score threshold) · LessWrong
(≥ karma threshold) · configured blogs.

## Pipeline

```
run.sh (launchd, daily 06:30)
  1. python -m src.scrape     → data/YYYY-MM-DD.json
  2. python -m src.generate   → digests/YYYY-MM-DD.md   (claude -p; template fallback)
  3. python -m src.feed       → docs/feed.xml + docs/digest/*.html
  4. git commit + push        → GitHub Pages serves docs/
```

## Setup

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# edit config.toml: thresholds, blog feeds, feed URLs
./install-schedule.sh        # installs the 06:30 launchd job
```

Requires: `claude` CLI logged in, `git` push access to this repo (Pages enabled,
serving `docs/` on `main`).

## Config (`config.toml`)

- `hackernews.min_score`, `lesswrong.min_karma` — inclusion thresholds
- `blogs.feeds` — list of RSS/Atom URLs to follow
- `digest.claude_model` — model for `claude -p` (default `sonnet`)

## Manual run / debugging

Each stage is independent:

```sh
.venv/bin/python -m src.scrape      # then inspect data/<today>.json
.venv/bin/python -m src.generate    # then read digests/<today>.md
.venv/bin/python -m src.feed        # then check docs/feed.xml
./run.sh                            # full pipeline; logs to logs/run-<date>.log
```

If `claude -p` fails (logged out, offline), `generate` writes a links-only fallback
digest so the feed never misses a day.
