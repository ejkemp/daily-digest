"""Stage 3: build docs/feed.xml (Atom) from the most recent digests."""

import datetime as dt
import re
import sys

import markdown
from feedgen.feed import FeedGenerator

from .common import DIGESTS_DIR, DOCS_DIR, load_config

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ max-width: 44rem; margin: 2rem auto; padding: 0 1rem;
       font: 17px/1.6 -apple-system, Georgia, serif; color: #222; }}
a {{ color: #1a5276; }}
h1, h2 {{ line-height: 1.25; }}
</style>
</head>
<body>
<p><a href="{root}/">&larr; All digests</a></p>
<h1>{title}</h1>
{body}
</body>
</html>
"""


def main() -> int:
    config = load_config()
    feed_cfg = config["feed"]
    keep = config["digest"]["keep_entries"]

    digest_files = sorted(
        p for p in DIGESTS_DIR.glob("*.md") if DATE_RE.match(p.stem)
    )[-keep:]
    if not digest_files:
        print("[feed] no digests found", file=sys.stderr)
        return 1

    fg = FeedGenerator()
    fg.id(feed_cfg["site_url"] + "/")
    fg.title(feed_cfg["title"])
    fg.author({"name": feed_cfg["author"]})
    fg.link(href=feed_cfg["feed_url"], rel="self")
    fg.link(href=feed_cfg["site_url"], rel="alternate")
    fg.language("en")

    pages_dir = DOCS_DIR / "digest"
    pages_dir.mkdir(parents=True, exist_ok=True)
    index_links = []

    # feedgen prepends entries, so iterate oldest-first to get newest at the top
    for path in digest_files:
        date = dt.date.fromisoformat(path.stem)
        # Stable timestamp per digest: publication morning, local time
        published = dt.datetime(
            date.year, date.month, date.day, 7, 0, tzinfo=dt.datetime.now().astimezone().tzinfo
        )
        html = markdown.markdown(path.read_text(), extensions=["extra"])
        title = f"Daily Digest — {date.strftime('%A, %B')} {date.day}, {date.year}"
        page_url = f"{feed_cfg['site_url']}/digest/{path.stem}.html"

        (pages_dir / f"{path.stem}.html").write_text(
            PAGE_TEMPLATE.format(title=title, body=html, root=feed_cfg["site_url"])
        )
        index_links.append(f'<li><a href="digest/{path.stem}.html">{title}</a></li>')

        fe = fg.add_entry()
        fe.id(f"{feed_cfg['site_url']}/digest/{path.stem}")
        fe.title(title)
        fe.link(href=page_url)
        fe.published(published)
        fe.updated(published)
        fe.content(html, type="html")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out = DOCS_DIR / "feed.xml"
    fg.atom_file(str(out), pretty=True)

    index_body = (
        f"<h2>Archive</h2>\n<ul>\n" + "\n".join(reversed(index_links)) + "\n</ul>\n"
        f'<p>Subscribe: <a href="{feed_cfg["feed_url"]}">Atom feed</a></p>'
    )
    (DOCS_DIR / "index.html").write_text(
        PAGE_TEMPLATE.format(title=feed_cfg["title"], body=index_body, root=feed_cfg["site_url"])
    )

    print(f"[feed] wrote {out} with {len(digest_files)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
