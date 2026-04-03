#!/usr/bin/env python3
"""Instagram Lead Generation Pipeline — CLI Entry Point.

Usage:
    python scrape.py                                          # use config.yaml defaults
    python scrape.py --hashtags "#travelcreator,#grouptrips"  # override hashtags
    python scrape.py --output leads.csv                       # custom output file
    python scrape.py --max-profiles 50                        # override profile limit
    python scrape.py --headless                               # run headless (less safe)
"""
import argparse
import signal
import sys

from src.config import load_config
from src.session import create_browser_session, close_browser_session, save_cookies
from src.scanner import scan_all_hashtags
from src.scraper import scrape_profiles
from src.writer import deduplicate_profiles, write_leads_csv


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape Instagram profiles of travel creators via hashtag discovery."
    )
    parser.add_argument(
        "--hashtags",
        type=str,
        default=None,
        help='Comma-separated hashtags (e.g., "#travel,#trips"). Overrides config.yaml.',
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output CSV filename.",
    )
    parser.add_argument(
        "--max-profiles",
        type=int,
        default=None,
        help="Max profiles to scrape per run. Overrides config.yaml.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=None,
        help="Run browser in headless mode (less safe, not recommended).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to custom config YAML file.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Build overrides from CLI args
    overrides = {}
    if args.hashtags:
        overrides["hashtags"] = [h.strip() for h in args.hashtags.split(",")]
    if args.output:
        overrides["output_file"] = args.output
    if args.max_profiles is not None:
        overrides["max_profiles"] = args.max_profiles
    if args.headless is not None:
        overrides["headless"] = args.headless

    # Load config
    config = load_config(config_path=args.config, overrides=overrides)

    hashtags = config["hashtags"]
    headless = config["settings"]["headless"]
    output_dir = config["output"]["directory"]
    output_prefix = config["output"]["filename_prefix"]
    custom_output = config["output"].get("custom_output_file")

    print("=" * 60)
    print("INSTAGRAM LEAD GENERATION PIPELINE")
    print("=" * 60)
    print(f"Hashtags: {', '.join(hashtags)}")
    print(f"Max profiles: {config['settings']['max_profiles_per_run']}")
    print(f"Headless: {headless}")
    print(f"Output: {output_dir}/")
    print("=" * 60)

    # Set up graceful shutdown
    collected_profiles = []
    pw = browser = None

    def graceful_shutdown(signum, frame):
        print("\n\n[main] Interrupted! Saving collected data...")
        if collected_profiles:
            deduped = deduplicate_profiles(collected_profiles)
            path = write_leads_csv(deduped, output_dir, output_prefix, custom_output)
            print(f"[main] Saved {len(deduped)} leads to: {path}")
        if pw and browser:
            close_browser_session(pw, browser)
        sys.exit(0)

    signal.signal(signal.SIGINT, graceful_shutdown)

    # Launch browser and login
    print("\n[main] Starting browser session...")
    pw, browser, context, page = create_browser_session(headless=headless)

    try:
        # Phase 1: Scan hashtags for usernames
        print("\n[main] Phase 1: Scanning hashtags for profiles...")
        username_sources = scan_all_hashtags(
            page,
            hashtags,
            max_posts_per_hashtag=config["settings"]["max_posts_per_hashtag"],
        )

        if not username_sources:
            print("[main] No profiles found. Exiting.")
            return

        # Phase 2: Scrape each profile
        print("\n[main] Phase 2: Scraping profile data...")
        collected_profiles = scrape_profiles(page, username_sources, config)

        # Phase 3: Save cookies and write CSV
        save_cookies(context)

        if collected_profiles:
            deduped = deduplicate_profiles(collected_profiles)
            path = write_leads_csv(deduped, output_dir, output_prefix, custom_output)
            print(f"\n{'=' * 60}")
            print(f"DONE! Saved {len(deduped)} leads to: {path}")
            print(f"{'=' * 60}")
        else:
            print("\n[main] No profile data collected.")

    except Exception as e:
        print(f"\n[main] Error: {e}")
        if collected_profiles:
            deduped = deduplicate_profiles(collected_profiles)
            path = write_leads_csv(deduped, output_dir, output_prefix, custom_output)
            print(f"[main] Emergency save: {len(deduped)} leads to: {path}")
        raise

    finally:
        close_browser_session(pw, browser)


if __name__ == "__main__":
    main()
