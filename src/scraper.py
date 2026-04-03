# src/scraper.py
import random
import time
from datetime import datetime
from src.extractor import extract_profile_data
from src.scanner import check_for_checkpoint


def _human_like_scroll(page):
    """Perform random scroll actions to mimic human behavior."""
    scroll_amount = random.randint(100, 400)
    page.mouse.wheel(0, scroll_amount)
    time.sleep(random.uniform(0.3, 0.8))
    # Sometimes scroll back up a bit
    if random.random() > 0.6:
        page.mouse.wheel(0, -random.randint(50, 150))
        time.sleep(random.uniform(0.2, 0.5))


def scrape_profile(page, username, source_hashtag=""):
    """Visit a single profile and extract all data.

    Args:
        page: Playwright page object (logged in)
        username: Instagram username to visit
        source_hashtag: Which hashtag discovered this profile

    Returns:
        dict with profile data, or None if profile couldn't be scraped
    """
    url = f"https://www.instagram.com/{username}/"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(random.uniform(2000, 4000))
    except Exception as e:
        print(f"  [@{username}] Failed to load profile: {e}")
        return None

    # Check for checkpoint
    if check_for_checkpoint(page):
        print(f"  [@{username}] CHECKPOINT DETECTED!")
        return "CHECKPOINT"

    # Check for 404 / page not found
    try:
        body_text = page.inner_text("body")
        if "Sorry, this page isn't available" in body_text:
            print(f"  [@{username}] Profile not found (404)")
            return None
    except Exception:
        pass

    # Check for private account
    is_private = False
    try:
        if "This account is private" in body_text or "This Account is Private" in body_text:
            is_private = True
            print(f"  [@{username}] Private account — extracting limited data")
    except Exception:
        pass

    # Human-like scroll before extracting
    _human_like_scroll(page)

    # Extract data
    try:
        data = extract_profile_data(page)
        data["source_hashtag"] = source_hashtag
        data["scraped_at"] = datetime.now().isoformat(timespec="seconds")
        return data
    except Exception as e:
        print(f"  [@{username}] Error extracting data: {e}")
        return None


def scrape_profiles(page, username_sources, config):
    """Scrape multiple profiles with rate limiting and safety checks.

    Args:
        page: Playwright page object (logged in)
        username_sources: dict of {username: source_hashtag}
        config: Config dict with settings

    Returns:
        list of profile data dicts
    """
    settings = config["settings"]
    max_profiles = settings["max_profiles_per_run"]
    delay_range = settings["delay_between_profiles"]
    cooldown_every = settings["cooldown_every"]
    cooldown_range = settings["cooldown_duration"]
    daily_cap = settings["daily_cap_warning"]

    profiles = []
    usernames = list(username_sources.items())[:max_profiles]

    print(f"\n[scraper] Scraping {len(usernames)} profiles (max: {max_profiles})")
    print(f"[scraper] Daily cap warning at {daily_cap} profiles\n")

    for i, (username, source_hashtag) in enumerate(usernames):
        print(f"[{i+1}/{len(usernames)}] Scraping @{username}...")

        result = scrape_profile(page, username, source_hashtag)

        if result == "CHECKPOINT":
            print("\n[scraper] CHECKPOINT DETECTED — stopping immediately.")
            print("[scraper] Saving data collected so far...")
            break

        if result is not None:
            profiles.append(result)
            print(f"  [@{username}] OK — {result.get('follower_count', 0)} followers")

        # Delay between profiles
        if i < len(usernames) - 1:
            delay = random.uniform(delay_range[0], delay_range[1])
            print(f"  Waiting {delay:.1f}s...")
            time.sleep(delay)

        # Cooldown every N profiles
        if (i + 1) % cooldown_every == 0 and i < len(usernames) - 1:
            cooldown = random.uniform(cooldown_range[0], cooldown_range[1])
            print(f"\n[scraper] Cooldown: pausing {cooldown:.0f}s after {i+1} profiles...\n")
            time.sleep(cooldown)

        # Daily cap warning
        if len(profiles) >= daily_cap:
            print(f"\n[scraper] WARNING: Reached daily cap of {daily_cap} profiles.")
            print("[scraper] Recommend stopping for today to avoid detection.")
            break

    print(f"\n[scraper] Done. Scraped {len(profiles)} profiles successfully.")
    return profiles
