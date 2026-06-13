You are writing today's edition of a personal daily digest newsletter. Below is a JSON
document of everything scraped in the last 24 hours: Wikipedia's "Topics in the news"
headlines, "Did you know" hooks, and "On this day" entries; high-scoring Hacker News
stories, and high-karma LessWrong posts.

Write the digest in Markdown with exactly this structure. Start output immediately, include nothing else:

Output these sections, as `##` headings, in this order — but OMIT any section whose
source has no items: `Topics in the News`, `Did You Know`, `On This Day`, `Hacker News`, `LessWrong`.
Do not write any overall summary or introduction before the first section.

Section guidelines:
- **Topics in the News**, **Did You Know**, and **On This Day** (from the Wikipedia data):
  each Wikipedia item carries a `section` field that is one of "Topics in the news",
  "Did you know", or "On this day" — render each item under the matching heading above.
  Include EVERY Wikipedia item, and reproduce its `title` text VERBATIM — do not summarize,
  shorten, drop, reword, or clean up the wording. List each as a single bullet linking the
  provided `url`. Format: `- [verbatim title text](url)`.
- **Hacker News**: one bullet per story worth reading — you may drop low-interest items
  (release-note churn, minor product announcements) but keep anything substantive.
  Format: `- [Title](url) — one-sentence description or why it matters. ([discussion](comments_url), N points)`
- **LessWrong**: one bullet per post: `- [Title](url) by Author — one-sentence summary. (N karma)`

Rules:
- Output ONLY the Markdown digest. No preamble, no code fences around the whole thing,
  no closing remarks.
- Never invent items, links, or facts not present in the data. Summaries must be grounded in the provided titles/excerpts/content.
- Preserve all URLs exactly as given.

Here is today's data:
