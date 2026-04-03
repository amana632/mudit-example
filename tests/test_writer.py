import csv
import os
import tempfile
import pytest
from src.writer import write_leads_csv, deduplicate_profiles

SAMPLE_PROFILES = [
    {
        "username": "travelguy",
        "display_name": "Travel Guy",
        "bio": "I travel",
        "follower_count": 5000,
        "following_count": 300,
        "post_count": 120,
        "profile_url": "https://www.instagram.com/travelguy/",
        "external_link": "https://travelguy.com",
        "is_verified": False,
        "account_category": "Travel Agency",
        "email": "hello@travelguy.com",
        "phone": "+1 555 1234",
        "whatsapp_link": "wa.me/15551234",
        "bio_urls": "https://travelguy.com",
        "scraped_at": "2026-04-03T10:00:00",
        "source_hashtag": "#travelcreator",
    },
    {
        "username": "adventurejane",
        "display_name": "Jane Adventures",
        "bio": "Hosting group trips worldwide",
        "follower_count": 12000,
        "following_count": 500,
        "post_count": 350,
        "profile_url": "https://www.instagram.com/adventurejane/",
        "external_link": "",
        "is_verified": True,
        "account_category": "",
        "email": None,
        "phone": None,
        "whatsapp_link": None,
        "bio_urls": "",
        "scraped_at": "2026-04-03T10:01:00",
        "source_hashtag": "#grouptrips",
    },
]


class TestWriteLeadsCsv:
    def test_write_csv_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_leads_csv(SAMPLE_PROFILES, output_dir=tmpdir, prefix="test")
            assert os.path.exists(path)

    def test_write_csv_has_correct_headers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_leads_csv(SAMPLE_PROFILES, output_dir=tmpdir, prefix="test")
            with open(path, "r") as f:
                reader = csv.reader(f)
                headers = next(reader)
            expected = [
                "username", "display_name", "bio", "follower_count",
                "following_count", "post_count", "profile_url", "external_link",
                "is_verified", "account_category", "email", "phone",
                "whatsapp_link", "bio_urls", "scraped_at", "source_hashtag",
            ]
            assert headers == expected

    def test_write_csv_has_correct_row_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_leads_csv(SAMPLE_PROFILES, output_dir=tmpdir, prefix="test")
            with open(path, "r") as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                rows = list(reader)
            assert len(rows) == 2

    def test_write_csv_custom_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_leads_csv(
                SAMPLE_PROFILES, output_dir=tmpdir, prefix="test", custom_filename="my_leads.csv"
            )
            assert path.endswith("my_leads.csv")

    def test_write_empty_profiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_leads_csv([], output_dir=tmpdir, prefix="test")
            with open(path, "r") as f:
                reader = csv.reader(f)
                next(reader)  # header
                rows = list(reader)
            assert len(rows) == 0


class TestDeduplicateProfiles:
    def test_removes_duplicate_usernames(self):
        profiles = [
            {"username": "alice", "source_hashtag": "#a"},
            {"username": "bob", "source_hashtag": "#b"},
            {"username": "alice", "source_hashtag": "#c"},
        ]
        result = deduplicate_profiles(profiles)
        assert len(result) == 2
        usernames = [p["username"] for p in result]
        assert "alice" in usernames
        assert "bob" in usernames

    def test_keeps_first_occurrence(self):
        profiles = [
            {"username": "alice", "source_hashtag": "#first"},
            {"username": "alice", "source_hashtag": "#second"},
        ]
        result = deduplicate_profiles(profiles)
        assert result[0]["source_hashtag"] == "#first"

    def test_empty_list(self):
        assert deduplicate_profiles([]) == []
