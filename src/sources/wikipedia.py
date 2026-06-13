"""Wikipedia Main Page highlights — three curated boxes scraped each day.

- **Topics in the news** ("In the news"): the day's biggest stories, from the
  Portal:Current events headline box. Each blurb is a one-sentence summary linking
  the relevant article.
- **Did you know**: trivia hooks drawn from recently created/expanded articles.
- **On this day**: notable events sharing today's calendar date.

Each item is tagged with a ``section`` field so the digest can render them under
separate headings. We reproduce whatever is in each box, with no deduplication — an
item may appear on multiple days while Wikipedia keeps it up.
"""

import datetime as dt
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from ..common import USER_AGENT

API = "https://en.wikipedia.org/w/api.php"
WIKI_BASE = "https://en.wikipedia.org"
CURRENT_EVENTS_PAGE = "Portal:Current events"
MAIN_PAGE = "Main Page"


def _clean(text: str) -> str:
    text = re.sub(r"\s*\([^)]*pictured\)", "", text)  # drop image captions
    text = re.sub(r"\s+([.,;])", r"\1", text)  # tighten " ." -> "."
    return text.strip()


def _parse_page(page: str) -> BeautifulSoup:
    resp = requests.get(
        API,
        params={
            "action": "parse",
            "page": page,
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
    return BeautifulSoup(body["parse"]["text"], "html.parser")


def _items_from_list(ul, section: str, today: str) -> list[dict]:
    """Turn a box's top-level <li> entries into tagged digest items."""
    items = []
    for li in ul.find_all("li", recursive=False):
        text = _clean(li.get_text(" ", strip=True))
        # The bolded link is the entry's main article; fall back to the first link.
        bold = li.find("b")
        link = (bold.find("a") if bold else None) or li.find("a")
        if not text or not link or not link.get("href"):
            continue
        items.append(
            {
                "source": "wikipedia",
                "section": section,
                "title": text,
                "url": urljoin(WIKI_BASE, link["href"]),
                "published": today,
            }
        )
    return items


def fetch(config: dict) -> list[dict]:
    today = dt.date.today().isoformat()
    items: list[dict] = []

    # Topics in the news — from the Portal:Current events headline box.
    portal = _parse_page(CURRENT_EVENTS_PAGE)
    box = portal.find("div", class_="p-current-events-headlines")
    if box is None:
        raise RuntimeError("Could not find 'Topics in the news' box on the portal page")
    ul = box.find("ul")
    if ul is None:
        raise RuntimeError("'Topics in the news' box has no list")
    items += _items_from_list(ul, "Topics in the news", today)

    # Did you know / On this day — from the Main Page.
    main = _parse_page(MAIN_PAGE)
    for div_id, section in (("mp-dyk", "Did you know"), ("mp-otd", "On this day")):
        div = main.find("div", id=div_id)
        ul = div.find("ul") if div else None
        if ul is None:
            raise RuntimeError(f"Could not find '{section}' list on the Main Page (#{div_id})")
        items += _items_from_list(ul, section, today)

    return items
