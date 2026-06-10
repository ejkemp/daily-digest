You are writing today's edition of a personal daily digest newsletter. Below is a JSON
document of everything scraped in the last 24 hours: Wikipedia's Current Events summary,
high-scoring Hacker News stories, high-karma LessWrong posts, and new posts from followed
blogs.

Write the digest in Markdown with exactly this structure:

1. Start with a short overview paragraph (2-4 sentences): the most important or
   interesting things across all sources today. No heading before it.
2. Then these sections, as `##` headings, in this order — but OMIT any section whose
   source has no items: `World News`, `Hacker News`, `LessWrong`, `Blogs`.

Section guidelines:
- **World News** (from the Wikipedia data): synthesize into 5-10 bullet points covering
  the most significant events. Group related events. Link to cited news sources where
  the data includes URLs.
- **Hacker News**: one bullet per story worth reading — you may drop low-interest items
  (release-note churn, minor product announcements) but keep anything substantive.
  Format: `- [Title](url) — one-sentence description or why it matters. ([discussion](comments_url), N points)`
- **LessWrong**: one bullet per post: `- [Title](url) by Author — one-sentence summary. (N karma)`
- **Blogs**: one bullet per post: `- [Title](url) (Blog Name) — one-to-two-sentence summary based on the excerpt.`

Rules:
- Output ONLY the Markdown digest. No preamble, no code fences around the whole thing,
  no closing remarks.
- Never invent items, links, or facts not present in the data. Summaries must be
  grounded in the provided titles/excerpts/content.
- Preserve all URLs exactly as given.
- Keep the whole digest scannable in under ~3 minutes.

Here is today's data:
