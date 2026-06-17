"""Best-effort readable-text extraction from an article URL.

Used so the digest LLM can summarize what a link actually says instead of guessing
from the title. This is deliberately dependency-light (BeautifulSoup only) and
forgiving: any fetch/parse problem returns None and the caller falls back to the
title alone.
"""

import re

import requests
from bs4 import BeautifulSoup

from .common import USER_AGENT

# Elements that never carry article prose; drop them before reading text.
_STRIP_TAGS = (
    "script", "style", "noscript", "template", "nav", "header", "footer",
    "aside", "form", "figure", "figcaption", "iframe", "svg",
)

_DEFAULT_MAX_CHARS = 4000
_DEFAULT_TIMEOUT = 15


def html_to_text(html: str, max_chars: int = _DEFAULT_MAX_CHARS) -> str:
    """Pull the main readable text out of an HTML document."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()

    # Prefer a semantic main-content container; fall back to the whole body.
    root = soup.find("article") or soup.find("main") or soup.body or soup

    blocks: list[str] = []
    for el in root.find_all(["h1", "h2", "h3", "p", "li", "blockquote", "pre"]):
        text = el.get_text(" ", strip=True)
        if len(text) >= 30:  # skip nav crumbs, button labels, stray fragments
            blocks.append(text)

    text = "\n\n".join(blocks).strip()
    if not text:  # nothing block-like found; last resort, take all text
        text = root.get_text(" ", strip=True)
    text = re.sub(r"[ \t]+", " ", text)
    return _truncate(text, max_chars)


def fetch_article_text(
    url: str, max_chars: int = _DEFAULT_MAX_CHARS, timeout: int = _DEFAULT_TIMEOUT
) -> str | None:
    """Fetch ``url`` and return its readable text, or None on any failure."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return None

    content_type = resp.headers.get("Content-Type", "")
    if "html" not in content_type and "xml" not in content_type:
        return None  # PDFs, images, etc. — not extractable here

    text = html_to_text(resp.text, max_chars)
    return text or None


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    # Cut on a word boundary so the model doesn't see a chopped token.
    cut = text.rfind(" ", 0, max_chars)
    if cut < max_chars // 2:
        cut = max_chars
    return text[:cut].rstrip() + " …"
