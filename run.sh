#!/bin/bash
# Daily digest pipeline: scrape -> generate -> feed -> publish.
# Run by launchd every morning; safe to run by hand too.
set -u
cd "$(dirname "$0")"

# launchd runs with a minimal PATH; make sure homebrew (claude, git) is on it
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"

mkdir -p logs
LOG="logs/run-$(date +%F).log"
exec >>"$LOG" 2>&1

echo "=== daily-digest run started $(date) ==="

PY=.venv/bin/python

if ! $PY -m src.scrape; then
  echo "FATAL: scrape produced no data; aborting"
  exit 1
fi

# generate falls back to a template digest internally on claude failure
$PY -m src.generate || { echo "FATAL: generate failed"; exit 1; }

$PY -m src.feed || { echo "FATAL: feed build failed"; exit 1; }

git add docs digests
if git diff --cached --quiet; then
  echo "nothing new to publish"
else
  git commit -m "digest $(date +%F)"
  git push || echo "WARNING: push failed; digest will publish on next successful run"
fi

echo "=== daily-digest run finished $(date) ==="
