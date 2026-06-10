"""
Unit tests for formatter.py.
These are pure functions (digest dict in, HTML string out), so no mocking needed.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from formatter import SENTIMENT_COLORS, format_evening, format_morning

SAMPLE_DIGEST: dict = {
    "top_stories": [
        {
            "title": "New Model Released",
            "what_it_is": "A new LLM",
            "why_it_matters": "It's faster",
            "what_changed": "50% faster than the previous generation",
            "url": "https://example.com/model",
            "source": "Test Source",
        }
    ],
    "new_models": [
        {
            "name": "TestModel-1",
            "type": "LLM",
            "what_it_is": "A test model",
            "improvement_over_previous": "Better benchmarks",
            "url": "https://example.com/testmodel",
        }
    ],
    "new_tools_frameworks": [],
    "community_discussions": [
        {
            "topic": "Is AGI near?",
            "sentiment": "skeptical",
            "key_points": "Mixed opinions on timelines",
            "source": "Reddit r/MachineLearning",
            "url": "https://example.com/thread",
        }
    ],
    "research_papers": [],
    "techniques_approaches": [],
    "trending_topics": ["LLMs", "agents"],
    "digest_summary": "A quiet day in AI.",
}

EMPTY_DIGEST: dict = {
    "top_stories": [],
    "new_models": [],
    "new_tools_frameworks": [],
    "community_discussions": [],
    "research_papers": [],
    "techniques_approaches": [],
    "trending_topics": [],
    "digest_summary": "",
}


class TestFormatMorning(unittest.TestCase):
    def test_includes_all_seven_sections(self) -> None:
        html = format_morning(SAMPLE_DIGEST)
        for heading in [
            "Top Stories", "New Models & Embeddings", "New Tools & Frameworks",
            "Community Pulse", "Research Papers", "Techniques & Approaches",
            "Trending Topics",
        ]:
            self.assertIn(heading, html)

    def test_renders_item_content(self) -> None:
        html = format_morning(SAMPLE_DIGEST)
        self.assertIn("New Model Released", html)
        self.assertIn("https://example.com/model", html)
        self.assertIn("A quiet day in AI.", html)

    def test_sentiment_badge_uses_correct_color(self) -> None:
        html = format_morning(SAMPLE_DIGEST)
        self.assertIn(SENTIMENT_COLORS["skeptical"], html)

    def test_empty_section_shows_placeholder(self) -> None:
        html = format_morning(SAMPLE_DIGEST)
        self.assertIn("No new tools today.", html)

    def test_fully_empty_digest_does_not_crash(self) -> None:
        html = format_morning(EMPTY_DIGEST)
        self.assertIn("Top Stories", html)


class TestFormatEvening(unittest.TestCase):
    def test_includes_four_sections(self) -> None:
        html = format_evening(SAMPLE_DIGEST)
        self.assertIn("New Since Morning", html)
        self.assertIn("Community Pulse", html)
        self.assertIn("Trending Topics", html)

    def test_handles_empty_digest(self) -> None:
        html = format_evening(EMPTY_DIGEST)
        self.assertIn("Nothing new since the morning digest.", html)


if __name__ == "__main__":
    unittest.main()
