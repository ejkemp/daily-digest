"""New posts from a configured list of blog RSS/Atom feeds."""

import datetime as dt
import time

import feedparser
from bs4 import BeautifulSoup

from ..common import USER_AGENT, load_seen, save_seen


def _entry_time(entry) -> dt.datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return dt.datetime.fromtimestamp(time.mktime(parsed), dt.UTC)


def _excerpt(entry, limit: int = 600) -> str:
    html = ""
    if entry.get("content"):
        html = entry.content[0].get("value", "")
    elif entry.get("summary"):
        html = entry.summary
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    return text[:limit]


def fetch(config: dict) -> list[dict]:
    cfg = config["blogs"]
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(hours=cfg["window_hours"])
    seen = load_seen()

    items = []
    errors = []
    for feed_url in cfg["feeds"]:
        parsed = feedparser.parse(feed_url, agent=USER_AGENT)
        if parsed.bozo and not parsed.entries:
            errors.append(f"{feed_url}: {parsed.get('bozo_exception')}")
            continue
        blog_title = parsed.feed.get("title", feed_url)
        for entry in parsed.entries:
            link = entry.get("link")
            if not link or link in seen:
                continue
            published = _entry_time(entry)
            if published and published < cutoff:
                continue
            seen.add(link)
            items.append(
                {
                    "source": "blogs",
                    "blog": blog_title,
                    "title": entry.get("title", "(untitled)"),
                    "url": link,
                    "published": published.isoformat() if published else None,
                    "excerpt": _excerpt(entry),
                }
            )

    save_seen(seen)
    if errors and not items and cfg["feeds"]:
        raise RuntimeError("All blog feeds failed: " + "; ".join(errors))
    return items
