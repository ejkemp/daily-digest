"""Stage 2: turn data/YYYY-MM-DD.json into digests/YYYY-MM-DD.md via headless Claude.

Falls back to a plain template digest if claude fails, so the feed never misses a day.
"""

import datetime as dt
import json
import subprocess
import sys
import tempfile

from .common import DATA_DIR, DIGESTS_DIR, PROMPTS_DIR, load_config


def build_prompt(data: dict) -> str:
    template = (PROMPTS_DIR / "digest.md").read_text()
    return template + "\n```json\n" + json.dumps(data, indent=1, ensure_ascii=False) + "\n```\n"


def run_claude(prompt: str, config: dict) -> str | None:
    cfg = config["digest"]
    try:
        # Run from an empty temp dir with all tools denied: this must be a pure
        # text transform, or claude may try to "edit the digest file" itself.
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    "claude", "-p",
                    "--model", cfg["claude_model"],
                    "--output-format", "text",
                    "--disallowedTools", "*",
                ],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=cfg["claude_timeout_seconds"],
                cwd=tmp,
            )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"[generate] claude invocation failed: {e}", file=sys.stderr)
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        print(f"[generate] claude exited {proc.returncode}: {proc.stderr[:500]}", file=sys.stderr)
        return None
    return proc.stdout.strip()


def template_digest(data: dict) -> str:
    """No-LLM fallback: titles and links grouped by section."""
    sections = {
        "wikipedia": "World News",
        "hackernews": "Hacker News",
        "lesswrong": "LessWrong",
        "blogs": "Blogs",
    }
    lines = ["*Automatic fallback digest (Claude was unavailable) — links only.*"]
    for key, heading in sections.items():
        items = data["sources"].get(key, {}).get("items", [])
        if not items:
            continue
        lines.append(f"\n## {heading}")
        for item in items:
            extra = ""
            if item.get("score") is not None:
                extra = f" ({item['score']} points)"
            lines.append(f"- [{item['title']}]({item['url']}){extra}")
    return "\n".join(lines)


def main() -> int:
    config = load_config()
    today = dt.date.today().isoformat()
    data_file = DATA_DIR / f"{today}.json"
    if not data_file.exists():
        print(f"[generate] no scrape data at {data_file}", file=sys.stderr)
        return 1
    data = json.loads(data_file.read_text())

    digest = run_claude(build_prompt(data), config)
    if digest is None:
        print("[generate] falling back to template digest", file=sys.stderr)
        digest = template_digest(data)

    DIGESTS_DIR.mkdir(parents=True, exist_ok=True)
    out = DIGESTS_DIR / f"{today}.md"
    out.write_text(digest + "\n")
    print(f"[generate] wrote {out} ({len(digest)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
