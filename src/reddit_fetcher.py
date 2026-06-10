"""
Reddit fetcher using PRAW (Python Reddit API Wrapper).
Fetches top posts from AI/ML subreddits for the past 24 hours.
PRAW handles Reddit OAuth and rate-limiting automatically — that's why we use it
instead of raw HTTP requests against the Reddit JSON API.
"""
import os

import praw
from dotenv import load_dotenv

load_dotenv()

# Subreddits to monitor — chosen for highest-signal AI/ML discussion.
# The tuple is (subreddit_name, post_limit) as specified in CLAUDE.md.
SUBREDDITS: list[tuple[str, int]] = [
    ("MachineLearning", 10),
    ("LocalLLaMA", 10),
    ("artificial", 10),
    ("OpenAI", 10),
    ("singularity", 8),
]


def fetch_reddit() -> list[dict]:
    """
    Fetch top posts from AI subreddits via the Reddit API.

    Returns a list of dicts with keys: title, url, summary, source, published.
    If REDDIT_CLIENT_ID is absent from env, logs a warning and returns [] —
    Reddit is optional enrichment, not a critical dependency.
    """
    # Guard: check credentials before attempting any network call
    client_id = os.getenv("REDDIT_CLIENT_ID")
    if not client_id:
        print("[Reddit] REDDIT_CLIENT_ID not set — skipping Reddit fetch")
        return []

    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    user_agent = os.getenv("REDDIT_USER_AGENT", "python:ai-digest-bot:v1.0")

    try:
        # read_only=True: we never post, comment, or vote — simplest auth flow
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            read_only=True,
        )
    except Exception as e:
        print(f"[Reddit] Failed to initialise PRAW client: {e}")
        return []

    all_items: list[dict] = []

    for subreddit_name, limit in SUBREDDITS:
        try:
            subreddit = reddit.subreddit(subreddit_name)
            # time_filter="day" gives the past 24 hours — ideal for a daily digest
            posts = subreddit.top(time_filter="day", limit=limit)

            count = 0
            for post in posts:
                # selftext is the body for text posts; link posts have empty selftext
                summary = post.selftext[:300]
                if len(post.selftext) > 300:
                    summary += "..."

                all_items.append({
                    "title": post.title,
                    "url": post.url,
                    "summary": summary,
                    "source": f"Reddit r/{subreddit_name}",
                    "published": "",  # reddit timestamps are unix ints — keep empty for consistency
                })
                count += 1

            print(f"[Reddit] Fetched {count} posts from r/{subreddit_name}")

        except Exception as e:
            # One subreddit failing must never crash the whole run
            print(f"[Reddit] Error fetching r/{subreddit_name}: {e}")
            continue

    return all_items
