"""
Nitter RSS fetcher — reads Twitter/X accounts without needing a Twitter API key.
Nitter is an open-source Twitter front-end that exposes RSS feeds per user.
We try multiple public instances per account because any one can go down at any time.
"""
import feedparser
from dotenv import load_dotenv

load_dotenv()

# Try primary first; fall back in order. Any instance can be down or rate-limited.
NITTER_INSTANCES: list[str] = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.1d4.us",
]

# Accounts with high AI/ML signal — mix of researchers, labs, and founders
ACCOUNTS: list[str] = [
    "karpathy",       # Andrej Karpathy — deep learning insights & commentary
    "ylecun",         # Yann LeCun — AI research debate & philosophy
    "AnthropicAI",    # Anthropic — Claude model announcements
    "OpenAI",         # OpenAI — GPT/o1/Sora releases
    "GoogleDeepMind", # DeepMind — Gemini & research papers
    "huggingface",    # HuggingFace — open-source model releases
    "sama",           # Sam Altman — OpenAI strategy & industry commentary
]

# Only surface tweets that mention these topics — filters personal/off-topic noise
KEYWORDS: list[str] = [
    "model", "paper", "release", "launch", "benchmark", "agent",
    "fine-tune", "embedding", "rag", "open source", "research",
    "dataset", "training", "inference",
]


def _is_relevant(text: str) -> bool:
    """
    Return True if text contains at least one AI/ML keyword.
    Case-insensitive because tweets vary in capitalisation.
    """
    lower = text.lower()
    return any(kw in lower for kw in KEYWORDS)


def _fetch_account(username: str) -> list[dict]:
    """
    Try each Nitter instance in order until one returns results for this account.
    Returns empty list if all instances fail — one user never crashes the whole run.
    """
    for instance in NITTER_INSTANCES:
        url = f"{instance}/{username}/rss"
        try:
            feed = feedparser.parse(url)

            # feedparser sets status=0 if the request never completed
            status = getattr(feed, "status", 0)
            if status not in (200, 301, 302):
                # This instance returned an error — try the next one
                continue

            if not feed.entries:
                # Instance is up but returned no content — try next
                continue

            items: list[dict] = []
            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")

                # Filter to AI/ML topics — avoids surfacing personal tweets
                if not _is_relevant(title + " " + summary):
                    continue

                items.append({
                    "title": title,
                    "url": entry.get("link", ""),
                    "summary": summary[:300],
                    "source": f"X: @{username}",
                    "published": entry.get("published", ""),
                })

            print(f"[Nitter] @{username}: {len(items)} relevant posts via {instance}")
            return items  # success — don't try other instances

        except Exception:
            # Silent: don't log every instance failure, only the final skip below
            continue

    # All instances exhausted for this account
    print(f"[Nitter] All instances failed for @{username} — skipping")
    return []


def fetch_nitter() -> list[dict]:
    """
    Fetch and keyword-filter tweets from all tracked AI/ML accounts via Nitter RSS.
    Returns combined list from all accounts. Per-account failures are skipped silently.
    """
    all_items: list[dict] = []

    for username in ACCOUNTS:
        items = _fetch_account(username)
        all_items.extend(items)

    return all_items
