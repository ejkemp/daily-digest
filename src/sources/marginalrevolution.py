"""Previous calendar day's Marginal Revolution posts, excluding assorted links."""

import datetime as dt
import re
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

import feedparser
import requests
from bs4 import BeautifulSoup

from ..common import USER_AGENT
from ..extract import html_to_text

FEED_URL = "https://marginalrevolution.com/feed"


def fetch(config: dict) -> list[dict]:
    timezone = ZoneInfo(config.get("marginalrevolution", {}).get("timezone", "America/New_York"))
    yesterday = dt.datetime.now(timezone).date() - dt.timedelta(days=1)
    content_cfg = config.get("content", {})
    items = {}
    # WordPress paginates its feed; continue until we have covered yesterday.
    for page in range(1, 21):
        response = requests.get(
            FEED_URL,
            params={"paged": page},
            headers={"User-Agent": USER_AGENT},
            timeout=content_cfg.get("fetch_timeout_seconds", 15),
        )
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        if feed.bozo:
            raise RuntimeError(f"Invalid Marginal Revolution feed: {feed.bozo_exception}")
        if not feed.entries:
            return sorted(items.values(), key=lambda item: item["published"])
        reached_older = False
        for entry in feed.entries:
            published = parsedate_to_datetime(entry.published)
            if published.tzinfo is None:
                raise ValueError("Marginal Revolution publication date has no timezone")
            date = published.astimezone(timezone).date()
            reached_older |= date < yesterday
            title = entry.title
            if date != yesterday or re.search(r"assorted\s+links", title, re.IGNORECASE):
                continue
            html = entry.get("content", [{}])[0].get("value") or entry.get("summary", "")
            soup = BeautifulSoup(html, "html.parser")
            # WordPress appends a self-link/attribution that is not post content.
            for paragraph in soup.find_all("p"):
                text = paragraph.get_text(" ", strip=True)
                if text.startswith("The post ") and "appeared first on" in text:
                    paragraph.decompose()
            items[entry.link] = {
                "source": "marginalrevolution",
                "title": title,
                "url": entry.link,
                "author": entry.get("author", "unknown"),
                "published": published.astimezone(dt.UTC).isoformat(),
                "content": html_to_text(str(soup), max_chars=content_cfg.get("max_chars", 4000)) or None,
            }
        if reached_older:
            return sorted(items.values(), key=lambda item: item["published"])
    raise RuntimeError("Marginal Revolution feed pagination did not reach the previous day")
