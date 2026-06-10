"""Shared helpers: config loading, paths, state."""

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DIGESTS_DIR = ROOT / "digests"
STATE_FILE = ROOT / "state" / "seen.json"
DOCS_DIR = ROOT / "docs"
PROMPTS_DIR = ROOT / "prompts"

USER_AGENT = "daily-digest (personal newsletter bot; ethankempj@gmail.com)"


def load_config() -> dict:
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def load_seen() -> set[str]:
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()


def save_seen(seen: set[str], cap: int = 5000) -> None:
    # Keep the file bounded; oldest entries fall off the front.
    urls = list(seen)[-cap:]
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(urls, indent=0))
