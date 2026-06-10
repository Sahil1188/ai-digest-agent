"""
Master fetcher — orchestrates all 20+ sources into a single list of new items.
Handles RSS feeds, scraped pages, Reddit (PRAW), and Nitter.
Deduplication is done against data/seen_urls.json so we never re-surface old content.
No database needed — a JSON file is sufficient for a single-process daily job.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from reddit_fetcher import fetch_reddit
from nitter_fetcher import fetch_nitter

load_dotenv()

# Resolve path relative to this file so it works both locally and in GitHub Actions
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SEEN_URLS_FILE = os.path.join(_DATA_DIR, "seen_urls.json")
MAX_SEEN_URLS = 2000   # cap to prevent unbounded file growth
DEDUP_DAYS = 7         # URLs expire after 7 days — allows recurring trending content to resurface

RSS_FEEDS: list[tuple[str, str]] = [
    ("ArXiv cs.AI",         "https://arxiv.org/rss/cs.AI"),
    ("ArXiv cs.LG",         "https://arxiv.org/rss/cs.LG"),
    ("ArXiv cs.CL",         "https://arxiv.org/rss/cs.CL"),
    ("HuggingFace Blog",    "https://huggingface.co/blog/feed.xml"),
    ("The Batch",           "https://www.deeplearning.ai/the-batch/rss"),
    ("Sebastian Raschka",   "https://magazine.sebastianraschka.com/feed"),
    ("Towards Data Science","https://towardsdatascience.com/feed"),
    ("MIT News AI",         "https://news.mit.edu/topic/artificial-intelligence-feed"),
    ("Google DeepMind",     "https://deepmind.google/blog/rss.xml"),
    ("Hacker News AI",      "https://hnrss.org/newest?q=AI+LLM+machine+learning&count=20"),
    ("Papers With Code",    "https://paperswithcode.com/latest#rss"),
    ("dev.to AI",           "https://dev.to/feed/tag/ai"),
    ("dev.to ML",           "https://dev.to/feed/tag/machinelearning"),
    ("Hashnode AI",         "https://hashnode.com/n/ai/rss"),
]

SCRAPED_PAGES: list[tuple[str, str]] = [
    ("OpenAI Blog",          "https://openai.com/blog"),
    ("Anthropic News",       "https://www.anthropic.com/news"),
    ("arxiv-sanity",         "https://arxiv-sanity-lite.com"),
    ("GitHub Trending Python","https://github.com/trending/python?since=daily"),
]


# ── Deduplication helpers ───────────────────────────────────────────────────
# Storage format: {"urls": {"https://...": "2026-06-09T12:00:00", ...}, "last_updated": "..."}
# Each URL maps to the ISO timestamp when we first sent it.
# URLs older than DEDUP_DAYS are treated as fresh — this lets GitHub Trending repos
# resurface after a week, and catches genuinely updated articles at the same URL.

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_seen_urls() -> dict[str, str]:
    """
    Load the url→timestamp map from JSON, dropping entries older than DEDUP_DAYS.
    Creates the file on first run. Returns {} on any read error.
    """
    os.makedirs(_DATA_DIR, exist_ok=True)

    if not os.path.exists(SEEN_URLS_FILE):
        _save_seen_urls({})
        return {}

    try:
        with open(SEEN_URLS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw: dict = data.get("urls", {})

        # Handle old list format from before this change — treat all as "seen now"
        if isinstance(raw, list):
            raw = {url: _now_iso() for url in raw}

        cutoff = datetime.now(timezone.utc) - timedelta(days=DEDUP_DAYS)

        # Drop expired entries so old URLs can resurface
        active = {
            url: ts for url, ts in raw.items()
            if datetime.fromisoformat(ts) > cutoff
        }

        expired = len(raw) - len(active)
        if expired:
            print(f"[Fetcher] Expired {expired} seen URLs older than {DEDUP_DAYS} days")

        return active

    except Exception:
        return {}


def _save_seen_urls(seen: dict[str, str]) -> None:
    """
    Persist the url→timestamp map, capping at MAX_SEEN_URLS (drop oldest first).
    """
    if len(seen) > MAX_SEEN_URLS:
        # Sort by timestamp ascending, keep the newest MAX_SEEN_URLS
        sorted_items = sorted(seen.items(), key=lambda x: x[1])
        seen = dict(sorted_items[-MAX_SEEN_URLS:])

    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(SEEN_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump({"urls": seen, "last_updated": _now_iso()}, f, indent=2)


# ── Source fetchers ─────────────────────────────────────────────────────────

def _fetch_rss(source_name: str, feed_url: str) -> list[dict]:
    """
    Parse one RSS/Atom feed. Returns up to 15 items.
    Returns [] on any error — one broken feed must not stop the run.
    """
    try:
        feed = feedparser.parse(feed_url)
        items: list[dict] = []

        for entry in feed.entries[:15]:
            url = entry.get("link", "")
            if not url:
                continue

            items.append({
                "title": entry.get("title", "No title"),
                "url": url,
                "summary": entry.get("summary", "")[:300],
                "source": source_name,
                "published": entry.get("published", ""),
            })

        print(f"[RSS] {source_name}: {len(items)} items")
        return items

    except Exception as e:
        print(f"[RSS] Error fetching {source_name}: {e}")
        return []


def _scrape_page(source_name: str, page_url: str) -> list[dict]:
    """
    Extract article links from a blog/news page via BeautifulSoup.
    We look for <a> tags with >=20-char anchor text — works for most blog layouts.
    Returns up to 10 items; returns [] on any error.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ai-digest-bot/1.0; +https://github.com)"}
        response = requests.get(page_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        items: list[dict] = []
        seen_titles: set[str] = set()
        parsed_base = urlparse(page_url)

        for link in soup.find_all("a", href=True)[:60]:
            title = link.get_text(strip=True)
            href: str = link["href"]

            # Skip navigation links and short anchor text
            if len(title) < 20 or href.startswith("#"):
                continue

            # Resolve relative URLs to absolute
            if href.startswith("/"):
                href = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
            elif not href.startswith("http"):
                continue

            if title in seen_titles:
                continue
            seen_titles.add(title)

            items.append({
                "title": title,
                "url": href,
                "summary": "",
                "source": source_name,
                "published": "",
            })

            if len(items) >= 10:
                break

        print(f"[Scrape] {source_name}: {len(items)} items")
        return items

    except Exception as e:
        print(f"[Scrape] Error scraping {source_name}: {e}")
        return []


# ── Main orchestrator ───────────────────────────────────────────────────────

def fetch_all() -> list[dict]:
    """
    Gather content from all 20+ sources, then deduplicate against seen_urls.json.
    Returns only items with URLs we haven't sent before.
    New URLs are persisted immediately so they won't appear in future runs.
    """
    seen_urls: dict[str, str] = _load_seen_urls()
    raw: list[dict] = []

    # 14 RSS feeds
    for name, url in RSS_FEEDS:
        raw.extend(_fetch_rss(name, url))

    # 4 scraped pages
    for name, url in SCRAPED_PAGES:
        raw.extend(_scrape_page(name, url))

    # Reddit via PRAW (skipped gracefully if creds missing)
    raw.extend(fetch_reddit())

    # Twitter via Nitter RSS
    raw.extend(fetch_nitter())

    print(f"\n[Fetcher] Total raw items across all sources: {len(raw)}")

    # Keep only items whose URL isn't in the active (non-expired) seen map
    new_items = [item for item in raw if item.get("url") and item["url"] not in seen_urls]

    print(f"[Fetcher] New items after deduplication: {len(new_items)}")

    # Record each new URL with the current timestamp so it expires in DEDUP_DAYS
    now = _now_iso()
    for item in new_items:
        if item.get("url"):
            seen_urls[item["url"]] = now

    _save_seen_urls(seen_urls)

    return new_items
