"""Hacker News stories above a score threshold, via the Algolia API."""

import datetime as dt

import requests

from ..common import USER_AGENT

API = "https://hn.algolia.com/api/v1/search_by_date"


def fetch(config: dict) -> list[dict]:
    cfg = config["hackernews"]
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
        items.append(
            {
                "source": "hackernews",
                "title": hit["title"],
                "url": hit.get("url") or comments_url,
                "comments_url": comments_url,
                "score": hit["points"],
                "num_comments": hit.get("num_comments", 0),
                "published": hit["created_at"],
            }
        )
    items.sort(key=lambda i: i["score"], reverse=True)
    return items
