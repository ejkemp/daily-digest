"""Wikipedia Current Events portal — yesterday's page (the most recent complete day)."""

import datetime as dt

import requests
from bs4 import BeautifulSoup

from ..common import USER_AGENT

API = "https://en.wikipedia.org/w/api.php"


def _portal_page_title(date: dt.date) -> str:
    # e.g. "Portal:Current events/2026 June 9" (no zero-padded day)
    return f"Portal:Current events/{date.year} {date.strftime('%B')} {date.day}"


def _html_to_lines(html: str) -> str:
    """Flatten the portal HTML into indented bullet lines, keeping link URLs."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["style", "script"]):
        tag.decompose()

    lines = []
    for el in soup.find_all(["p", "li"]):
        # Category headers are bold paragraphs like "Armed conflicts and attacks"
        text = el.get_text(" ", strip=True)
        if not text or text.split(" ", 1)[0] in ("edit", "history", "watch"):
            continue
        if el.name == "p":
            lines.append(f"\n## {text}")
        else:
            # Only keep leaf bullets to avoid duplicating nested text
            if el.find("li"):
                continue
            ref = el.find("a", class_="external")
            suffix = f" [{ref['href']}]" if ref and ref.get("href") else ""
            lines.append(f"- {text}{suffix}")
    return "\n".join(lines)


def fetch(config: dict) -> list[dict]:
    date = dt.date.today() - dt.timedelta(days=1)
    title = _portal_page_title(date)
    resp = requests.get(
        API,
        params={
            "action": "parse",
            "page": title,
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

    text = _html_to_lines(body["parse"]["text"])
    url = "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")
    return [
        {
            "source": "wikipedia",
            "title": f"Wikipedia Current Events — {date.strftime('%B')} {date.day}, {date.year}",
            "url": url,
            "published": date.isoformat(),
            "content": text,
        }
    ]
