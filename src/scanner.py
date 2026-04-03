# src/scanner.py
import random
import time


def check_for_checkpoint(page):
    """Check if Instagram is showing a challenge/checkpoint screen."""
    checkpoint_indicators = [
        "challenge",
        "/accounts/suspended",
        "suspicious activity",
        "confirm your identity",
    ]
    page_url = page.url.lower()
    for indicator in checkpoint_indicators:
        if indicator in page_url:
            return True

    try:
        body_text = page.inner_text("body")
        for indicator in ["Confirm your identity", "Suspicious Login Attempt", "We detected an unusual login"]:
            if indicator in body_text:
                return True
    except Exception:
        pass

    return False


def scan_hashtag(page, hashtag, max_posts=50):
    """Visit a hashtag page and collect unique usernames from recent posts.

    Args:
        page: Playwright page object (must be logged in)
        hashtag: Hashtag string (with or without #)
        max_posts: Max number of posts to scan

    Returns:
        list of unique username strings
    """
    tag = hashtag.lstrip("#").strip()
    url = f"https://www.instagram.com/explore/tags/{tag}/"

    print(f"\n[scanner] Scanning hashtag: #{tag}")
    page.goto(url, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(random.uniform(2000, 4000))

    if check_for_checkpoint(page):
        print("[scanner] CHECKPOINT DETECTED! Stopping scan.")
        return []

    # Check if hashtag page loaded
    if "explore/tags" not in page.url:
        print(f"[scanner] Hashtag page did not load for #{tag}, skipping.")
        return []

    usernames = set()

    # Collect links to posts from the grid
    # Instagram hashtag pages show a grid of posts; each links to /p/ or /reel/
    post_links = page.query_selector_all("article a[href*='/p/'], article a[href*='/reel/']")
    if not post_links:
        # Fallback: try broader selector
        post_links = page.query_selector_all("a[href*='/p/'], a[href*='/reel/']")

    post_hrefs = []
    for link in post_links[:max_posts]:
        href = link.get_attribute("href")
        if href and ("/p/" in href or "/reel/" in href):
            post_hrefs.append(href)

    post_hrefs = list(dict.fromkeys(post_hrefs))  # dedupe preserving order
    print(f"[scanner] Found {len(post_hrefs)} posts on #{tag}")

    # Visit each post and extract the author username
    for i, href in enumerate(post_hrefs[:max_posts]):
        if check_for_checkpoint(page):
            print("[scanner] CHECKPOINT DETECTED! Stopping scan.")
            break

        try:
            full_url = f"https://www.instagram.com{href}" if href.startswith("/") else href
            page.goto(full_url, wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(random.uniform(1000, 2500))

            # Extract username from post page — the first link in the header area
            author_el = page.query_selector(
                "article header a[href*='/'], "
                "header a[role='link'][href*='/']"
            )
            if author_el:
                author_href = author_el.get_attribute("href") or ""
                username = author_href.strip("/").split("/")[-1]
                if username and username not in ("p", "reel", "explore", ""):
                    usernames.add(username)
                    print(f"  [{i+1}/{len(post_hrefs)}] Found: @{username}")

        except Exception as e:
            print(f"  [{i+1}/{len(post_hrefs)}] Error extracting from post: {e}")
            continue

        # Small delay between posts
        time.sleep(random.uniform(0.5, 1.5))

    print(f"[scanner] Collected {len(usernames)} unique profiles from #{tag}")
    return list(usernames)


def scan_all_hashtags(page, hashtags, max_posts_per_hashtag=50):
    """Scan multiple hashtags and return combined unique usernames.

    Args:
        page: Playwright page object
        hashtags: List of hashtag strings
        max_posts_per_hashtag: Max posts to scan per hashtag

    Returns:
        dict mapping username -> source_hashtag (first hashtag that found them)
    """
    username_sources = {}

    for hashtag in hashtags:
        usernames = scan_hashtag(page, hashtag, max_posts=max_posts_per_hashtag)
        for username in usernames:
            if username not in username_sources:
                username_sources[username] = hashtag

        # Delay between hashtags
        if hashtag != hashtags[-1]:
            delay = random.uniform(3, 6)
            print(f"[scanner] Waiting {delay:.1f}s before next hashtag...")
            time.sleep(delay)

    print(f"\n[scanner] Total unique profiles found: {len(username_sources)}")
    return username_sources
