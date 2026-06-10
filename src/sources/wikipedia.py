"""Wikipedia "Topics in the news" — the curated headline box atop the Current events portal.

This is the small hand-picked set of the day's biggest stories (the same blurbs shown
in the Main Page "In the news" box), not the exhaustive daily event log. Each blurb is
already a one-sentence summary linking the relevant Wikipedia article.

We reproduce whatever is in the box each day, with no deduplication — a headline may
appear on multiple days while Wikipedia keeps it in the box.
"""

import datetime as dt
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from ..common import USER_AGENT

API = "https://en.wikipedia.org/w/api.php"
WIKI_BASE = "https://en.wikipedia.org"
PAGE = "Portal:Current events"


def _clean(text: str) -> str:
    text = re.sub(r"\s*\([^)]*pictured\)", "", text)  # drop image captions
    text = re.sub(r"\s+([.,;])", r"\1", text)  # tighten " ." -> "."
    return text.strip()


def fetch(config: dict) -> list[dict]:
    resp = requests.get(
        API,
        params={
            "action": "parse",
            "page": PAGE,
            "prop": "text",
            "format": "json",
            "formatversion": "2",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        raise RuntimeError(f"Wikipedia API error: {body['error'].get('info')}")

    soup = BeautifulSoup(body["parse"]["text"], "html.parser")
    box = soup.find("div", class_="p-current-events-headlines")
    if box is None:
        raise RuntimeError("Could not find 'Topics in the news' box on the portal page")
    ul = box.find("ul")
    if ul is None:
        raise RuntimeError("'Topics in the news' box has no list")

    today = dt.date.today().isoformat()
    items = []
    for li in ul.find_all("li", recursive=False):
        text = _clean(li.get_text(" ", strip=True))
        # The bolded link is the blurb's main article; fall back to the first link.
        bold = li.find("b")
        link = (bold.find("a") if bold else None) or li.find("a")
        if not text or not link or not link.get("href"):
            continue
        url = urljoin(WIKI_BASE, link["href"])
        items.append(
            {
                "source": "wikipedia",
                "title": text,
                "url": url,
                "published": today,
            }
        )

    return items
