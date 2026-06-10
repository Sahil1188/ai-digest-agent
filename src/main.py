"""
Entry point for the AI Digest system.
Pipeline: fetch all sources → summarize with LLM → format HTML → send (or preview).

Usage:
  python src/main.py --time morning
  python src/main.py --time evening
  python src/main.py --time morning --dry-run   # saves HTML to /tmp, no email sent
"""
import argparse
import os
import sys
import tempfile

# Add src/ to sys.path so sibling imports work when invoked from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from fetcher import fetch_all
from formatter import format_evening, format_morning
from mailer import build_subject, send_email
from summarizer import summarize

load_dotenv()


def main() -> None:
    """
    Orchestrate the full digest pipeline.
    --dry-run skips email delivery and saves an HTML file for browser preview instead.
    """
    parser = argparse.ArgumentParser(
        description="AI Digest — daily AI/ML email digest runner"
    )
    parser.add_argument(
        "--time",
        choices=["morning", "evening"],
        required=True,
        help="Which digest edition to generate: morning (7 sections) or evening (4 sections)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip sending email; save HTML preview to /tmp/digest_preview_{time}.html",
    )
    args = parser.parse_args()

    print(f"\n{'=' * 55}")
    print(f"  AI Digest — {args.time.upper()} run")
    print(f"{'=' * 55}\n")

    # ── Step 1: Fetch ───────────────────────────────────────────
    print("[Main] Step 1/4 — Fetching from all sources...")
    items = fetch_all()

    if not items:
        print("[Main] No new items found — all sources either failed or returned only seen URLs.")
        print("[Main] Continuing with an empty digest (email will still be sent).")
    else:
        print(f"[Main] {len(items)} new items ready for summarisation.\n")

    # ── Step 2: Summarize ───────────────────────────────────────
    print("[Main] Step 2/4 — Summarising with Gemini / Groq...")
    digest = summarize(items, digest_time=args.time)

    # ── Step 3: Format ──────────────────────────────────────────
    print("\n[Main] Step 3/4 — Formatting HTML email...")
    html = format_morning(digest) if args.time == "morning" else format_evening(digest)

    # ── Step 4: Send or preview ─────────────────────────────────
    if args.dry_run:
        preview_path = os.path.join(tempfile.gettempdir(), f"digest_preview_{args.time}.html")
        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\n[Main] DRY RUN — email NOT sent.")
        print(f"[Main] HTML preview saved to: {preview_path}")
        print(f"[Main] Open in browser:        file://{preview_path}")
    else:
        print("\n[Main] Step 4/4 — Sending email...")
        subject = build_subject(args.time)
        success = send_email(subject, html)
        if not success:
            print(f"\n[Main] Failed to send {args.time} digest — see error above.")
            sys.exit(1)
        print(f"\n[Main] {args.time.capitalize()} digest sent successfully!")

    print(f"\n[Main] Done.\n")


if __name__ == "__main__":
    main()
