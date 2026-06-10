"""
Unit tests for the deduplication logic in fetcher.py.
Each test redirects SEEN_URLS_FILE to a temp file so the real
data/seen_urls.json is never touched.
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import fetcher


class TestSeenUrlsDedup(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self._original_dir = fetcher._DATA_DIR
        self._original_file = fetcher.SEEN_URLS_FILE
        fetcher._DATA_DIR = self.tmpdir.name
        fetcher.SEEN_URLS_FILE = os.path.join(self.tmpdir.name, "seen_urls.json")

    def tearDown(self) -> None:
        fetcher._DATA_DIR = self._original_dir
        fetcher.SEEN_URLS_FILE = self._original_file
        self.tmpdir.cleanup()

    def test_creates_file_on_first_run(self) -> None:
        seen = fetcher._load_seen_urls()
        self.assertEqual(seen, {})
        self.assertTrue(os.path.exists(fetcher.SEEN_URLS_FILE))

    def test_round_trip_save_and_load(self) -> None:
        fetcher._save_seen_urls({"https://a.com": fetcher._now_iso()})
        seen = fetcher._load_seen_urls()
        self.assertIn("https://a.com", seen)

    def test_expired_urls_are_dropped(self) -> None:
        old_ts = (datetime.now(timezone.utc) - timedelta(days=fetcher.DEDUP_DAYS + 1)).isoformat()
        fresh_ts = fetcher._now_iso()
        fetcher._save_seen_urls({
            "https://old.com": old_ts,
            "https://new.com": fresh_ts,
        })
        seen = fetcher._load_seen_urls()
        self.assertNotIn("https://old.com", seen)
        self.assertIn("https://new.com", seen)

    def test_migrates_legacy_list_format(self) -> None:
        # Older versions stored {"urls": [...]} as a plain list, not a dict
        with open(fetcher.SEEN_URLS_FILE, "w", encoding="utf-8") as f:
            json.dump({"urls": ["https://legacy.com"], "last_updated": ""}, f)

        seen = fetcher._load_seen_urls()
        self.assertIn("https://legacy.com", seen)

    def test_max_seen_urls_cap(self) -> None:
        seen = {f"https://example.com/{i}": fetcher._now_iso() for i in range(fetcher.MAX_SEEN_URLS + 10)}
        fetcher._save_seen_urls(seen)

        with open(fetcher.SEEN_URLS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertLessEqual(len(data["urls"]), fetcher.MAX_SEEN_URLS)


if __name__ == "__main__":
    unittest.main()
