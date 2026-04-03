import csv
import os
from datetime import datetime
from pathlib import Path

CSV_COLUMNS = [
    "username", "display_name", "bio", "follower_count",
    "following_count", "post_count", "profile_url", "external_link",
    "is_verified", "account_category", "email", "phone",
    "whatsapp_link", "bio_urls", "scraped_at", "source_hashtag",
]


def deduplicate_profiles(profiles):
    """Remove duplicate profiles by username, keeping the first occurrence."""
    seen = set()
    unique = []
    for profile in profiles:
        username = profile.get("username")
        if username not in seen:
            seen.add(username)
            unique.append(profile)
    return unique


def write_leads_csv(profiles, output_dir="./output", prefix="leads", custom_filename=None):
    """Write profiles to a timestamped CSV file. Returns the file path."""
    os.makedirs(output_dir, exist_ok=True)

    if custom_filename:
        filename = custom_filename
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.csv"

    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for profile in profiles:
            writer.writerow(profile)

    return filepath
