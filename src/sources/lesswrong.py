"""LessWrong posts above a karma threshold, via the public GraphQL API.

The query also pulls each post's body (``contents.html``) so the digest can
summarize the actual argument rather than guessing from the title.
"""

import datetime as dt

import requests

from ..common import USER_AGENT
from ..extract import html_to_text

API = "https://www.lesswrong.com/graphql"

QUERY = """
{
  posts(input: {terms: {view: "new", limit: 100}}) {
    results {
      title
      pageUrl
      baseScore
      postedAt
      user { displayName }
      contents { html }
    }
  }
}
"""


def fetch(config: dict) -> list[dict]:
    cfg = config["lesswrong"]
    max_chars = config.get("content", {}).get("max_chars", 4000)
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(hours=cfg["window_hours"])

    resp = requests.post(
        API,
        json={"query": QUERY},
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    if "errors" in body:
        raise RuntimeError(f"LessWrong GraphQL error: {body['errors']}")

    items = []
    for post in body["data"]["posts"]["results"]:
        posted = dt.datetime.fromisoformat(post["postedAt"].replace("Z", "+00:00"))
        if posted < cutoff or post["baseScore"] < cfg["min_karma"]:
            continue
        user = post.get("user") or {}
        contents = post.get("contents") or {}
        html = contents.get("html")
        items.append(
            {
                "source": "lesswrong",
                "title": post["title"],
                "url": post["pageUrl"],
                "score": post["baseScore"],
                "author": user.get("displayName", "unknown"),
                "published": post["postedAt"],
                "content": html_to_text(html, max_chars=max_chars) if html else None,
            }
        )
    items.sort(key=lambda i: i["score"], reverse=True)
    return items[: cfg["max_items"]]
