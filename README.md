# Daily Digest

A personal daily newsletter. Every morning a launchd job on the Mac Mini scrapes a set of
sources, has Claude (headless `claude -p`) write a digest, and publishes it as an Atom
feed via GitHub Pages.

**Sources:** Wikipedia Main Page (Topics in the news · Did you know · On this day) ·
Hacker News (≥ score threshold) · LessWrong (≥ karma threshold).

## Pipeline

```
run.sh (launchd, daily 06:30)
  1. python -m src.scrape     → data/YYYY-MM-DD.json
  2. python -m src.generate   → digests/YYYY-MM-DD.md   (claude -p; template fallback)
  3. python -m src.feed       → docs/feed.xml + docs/digest/*.html
  4. git commit + push        → GitHub Pages serves docs/
```

## Deploying on the Mac Mini (the always-on runner)

Run these on the Mini itself. The job should run on exactly one machine.

```sh
# 1. Prerequisites (Homebrew assumed installed)
brew install python git gh
#    Install Claude Code and log in (the digest uses `claude -p` on your subscription):
#    install per https://docs.claude.com, then run `claude` once and complete login.

# 2. GitHub auth so the nightly `git push` works
gh auth login --web --git-protocol https

# 3. Clone and set up
git clone https://github.com/ejkemp/daily-digest.git
cd daily-digest
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 4. Smoke-test the whole pipeline by hand
./run.sh
cat "logs/run-$(date +%F).log"        # should end with "run finished"; check for a pushed commit

# 5. Install the daily 06:30 schedule (generates the launchd plist for this clone)
./install-schedule.sh
launchctl kickstart "gui/$(id -u)/com.ethan.daily-digest"   # trigger one run now to confirm
```

Notes:
- **One machine only.** If you ever set this up elsewhere, uninstall there with
  `launchctl bootout "gui/$(id -u)/com.ethan.daily-digest"` so two machines don't both push.
- **The Mini must be awake at 06:30.** If it sleeps, the job runs on next wake. Keep it
  from sleeping (System Settings → Energy, or `caffeinate`/`pmset`) for on-time delivery.
- If `claude` ever gets logged out, the digest still publishes a links-only fallback
  (visibly tagged) — that's your cue to run `claude` and re-auth.
- **Don't clone into `~/Documents`, `~/Desktop`, or `~/Downloads`.** Those are TCC-protected,
  so the launchd agent is denied (`run.sh: Operation not permitted`, exit 126) even though a
  manual `./run.sh` works. Keep the repo somewhere like `~/daily-digest`.

## Operation

Once installed, the job is a launchd **agent** — `launchd` runs it, not your terminal:
- **No terminal needed.** You can close the terminal / shell session; the schedule keeps running.
- **Survives reboots.** The plist lives at `~/Library/LaunchAgents/com.ethan.daily-digest.plist`
  and reloads automatically when you log in.
- **Requires the Mac on and your user logged in** at 06:30 (it's a per-user GUI agent), plus
  awake — see the sleep note above.

Check it's still scheduled and see the last run's result:

```sh
launchctl print "gui/$(id -u)/com.ethan.daily-digest" | grep -iE 'state|runs|last exit'
```

## Config (`config.toml`)

- `hackernews.min_score`, `lesswrong.min_karma` — inclusion thresholds
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
