"""Stage 1: run all sources and write data/YYYY-MM-DD.json."""

import datetime as dt
import json
import sys
import traceback

from .common import DATA_DIR, load_config
from .sources import blogs, hackernews, lesswrong, wikipedia

SOURCES = {
    "wikipedia": wikipedia.fetch,
    "hackernews": hackernews.fetch,
    "lesswrong": lesswrong.fetch,
    "blogs": blogs.fetch,
}


def main() -> int:
    config = load_config()
    today = dt.date.today().isoformat()
    result = {
        "date": today,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "sources": {},
    }

    any_ok = False
    for name, fetch in SOURCES.items():
        try:
            items = fetch(config)
            result["sources"][name] = {"ok": True, "items": items}
            any_ok = True
            print(f"[scrape] {name}: {len(items)} items")
        except Exception as e:
            traceback.print_exc()
            result["sources"][name] = {"ok": False, "error": str(e), "items": []}
            print(f"[scrape] {name}: FAILED ({e})", file=sys.stderr)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / f"{today}.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[scrape] wrote {out}")

    return 0 if any_ok else 1


if __name__ == "__main__":
    sys.exit(main())
