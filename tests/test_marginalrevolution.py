import datetime as dt
import unittest
from unittest.mock import patch

from src.generate import template_digest
from src.sources import marginalrevolution as mr


def feed(posts):
    items = "".join(
        f"<item><title>{title}</title><link>https://example.com/{index}</link>"
        f"<pubDate>{date}</pubDate><description>&lt;p&gt;A substantive post body "
        "for a grounded summary.&lt;/p&gt;&lt;p&gt;The post Title appeared first on "
        "Marginal REVOLUTION.&lt;/p&gt;</description></item>"
        for index, (title, date) in enumerate(posts)
    )
    return f"<rss version='2.0'><channel><title>MR</title>{items}</channel></rss>".encode()


class MarginalRevolutionTests(unittest.TestCase):
    @patch.object(mr.requests, "get")
    @patch.object(mr.dt, "datetime", wraps=dt.datetime)
    def test_calendar_boundaries_exclusions_and_pagination(self, clock, get):
        clock.now.return_value = dt.datetime(2026, 10, 8, 6, 30, tzinfo=dt.UTC)
        pages = [feed([
            ("Today", "Thu, 08 Oct 2026 04:00:00 +0000"),
            ("Wednesday ASSORTED LINKS", "Wed, 07 Oct 2026 17:00:00 +0000"),
            ("Yesterday late", "Thu, 08 Oct 2026 03:59:59 +0000"),
        ]), feed([
            ("Yesterday early", "Wed, 07 Oct 2026 04:00:00 +0000"),
            ("Too old", "Wed, 07 Oct 2026 03:59:59 +0000"),
        ])]
        get.return_value.content = pages[0]
        def response(*args, **kwargs):
            from unittest.mock import Mock
            return Mock(content=pages[kwargs["params"]["paged"] - 1])
        get.side_effect = response
        items = mr.fetch({})
        self.assertEqual([item["title"] for item in items], ["Yesterday early", "Yesterday late"])
        self.assertEqual(get.call_count, 2)
        self.assertIn("substantive post body", items[0]["content"])
        self.assertNotIn("appeared first on", items[0]["content"])

    def test_fallback_section_and_empty_source(self):
        data = {"sources": {"marginalrevolution": {"items": [
            {"title": "A post", "url": "https://example.com/post"}
        ]}}}
        self.assertIn("## Marginal Revolution\n- [A post](https://example.com/post)", template_digest(data))
        self.assertNotIn("Marginal Revolution", template_digest({"sources": {}}))


if __name__ == "__main__":
    unittest.main()
