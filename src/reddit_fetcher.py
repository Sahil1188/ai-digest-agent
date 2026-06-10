"""
Reddit fetcher — pulls top daily posts from AI/ML subreddits via Reddit's
public RSS feeds (old.reddit.com), the same read-only RSS approach used in
nitter_fetcher.py for Twitter/X.

Why RSS instead of the official API: as of late 2025, Reddit requires a
multi-week pre-approval process for ANY API access, including hobby
projects. Public RSS feeds need no registration and no credentials.
"""
import requests
import feedparser
from bs4 import BeautifulSoup

# (subreddit, post_limit) — chosen for highest-signal AI/ML discussion
SUBREDDITS: list[tuple[str, int]] = [
    ("MachineLearning", 10),
    ("LocalLLaMA", 10),
    ("artificial", 10),
    ("OpenAI", 10),
    ("singularity", 8),
]

# Reddit blocks requests without a browser-like User-Agent (returns 429/403)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ai-digest-agent/1.0; +https://github.com)"}


def _clean_summary(html_summary: str) -> str:
    """
    Reddit's RSS summary field is an HTML blob (thumbnail table + comment link).
    Strip the markup down to plain text and trim to 300 chars per CLAUDE.md spec.
    """
    text = BeautifulSoup(html_summary, "lxml").get_text(separator=" ", strip=True)
    return text[:300]


def fetch_reddit() -> list[dict]:
    """
    Fetch top-of-day posts from AI/ML subreddits via public RSS feeds.

    Returns a list of dicts with keys: title, url, summary, source, published.
    One subreddit failing (rate limit, network error) never stops the others —
    we log and move on, returning whatever succeeded.
    """
    all_items: list[dict] = []

    for subreddit, limit in SUBREDDITS:
        url = f"https://old.reddit.com/r/{subreddit}/top/.rss?t=day&limit={limit}"

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            count = 0
            for entry in feed.entries[:limit]:
                all_items.append({
                    "title": entry.get("title", "No title"),
                    "url": entry.get("link", ""),
                    "summary": _clean_summary(entry.get("summary", "")),
                    "source": f"Reddit r/{subreddit}",
                    "published": entry.get("published", ""),
                })
                count += 1

            print(f"[Reddit] Fetched {count} posts from r/{subreddit}")

        except Exception as e:
            print(f"[Reddit] Error fetching r/{subreddit}: {e}")
            continue

    return all_items
