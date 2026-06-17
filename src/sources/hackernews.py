"""Hacker News stories above a score threshold, via the Algolia API.

For each story we also fetch the linked article's readable text so the digest can
summarize what it actually says. Text posts (Ask/Show HN with no external link)
carry their body inline in the Algolia response, so we use that directly.
"""

import datetime as dt

import requests

from ..common import USER_AGENT
from ..extract import fetch_article_text, html_to_text

API = "https://hn.algolia.com/api/v1/search_by_date"


def fetch(config: dict) -> list[dict]:
    cfg = config["hackernews"]
    content_cfg = config.get("content", {})
    max_chars = content_cfg.get("max_chars", 4000)
    timeout = content_cfg.get("fetch_timeout_seconds", 15)

    cutoff = int(
        (dt.datetime.now(dt.UTC) - dt.timedelta(hours=cfg["window_hours"])).timestamp()
    )
    resp = requests.get(
        API,
        params={
            "tags": "story",
            "numericFilters": f"points>={cfg['min_score']},created_at_i>={cutoff}",
            "hitsPerPage": cfg["max_items"],
        },
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()

    items = []
    for hit in resp.json()["hits"]:
        comments_url = f"https://news.ycombinator.com/item?id={hit['objectID']}"
        url = hit.get("url") or comments_url

        if hit.get("url"):
            content = fetch_article_text(url, max_chars=max_chars, timeout=timeout)
        elif hit.get("story_text"):
            # Self/Ask/Show HN post: body is inline HTML, no external page to scrape.
            content = html_to_text(hit["story_text"], max_chars=max_chars)
        else:
            content = None

        items.append(
            {
                "source": "hackernews",
                "title": hit["title"],
                "url": url,
                "comments_url": comments_url,
                "score": hit["points"],
                "num_comments": hit.get("num_comments", 0),
                "published": hit["created_at"],
                "content": content,
            }
        )
    items.sort(key=lambda i: i["score"], reverse=True)
    return items
