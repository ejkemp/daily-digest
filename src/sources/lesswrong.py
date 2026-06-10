"""LessWrong posts above a karma threshold, via the public GraphQL API."""

import datetime as dt

import requests

from ..common import USER_AGENT

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
    }
  }
}
"""


def fetch(config: dict) -> list[dict]:
    cfg = config["lesswrong"]
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
        items.append(
            {
                "source": "lesswrong",
                "title": post["title"],
                "url": post["pageUrl"],
                "score": post["baseScore"],
                "author": user.get("displayName", "unknown"),
                "published": post["postedAt"],
            }
        )
    items.sort(key=lambda i: i["score"], reverse=True)
    return items[: cfg["max_items"]]
