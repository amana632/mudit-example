import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync


SESSIONS_DIR = Path(__file__).parent.parent / "sessions"
COOKIES_FILE = SESSIONS_DIR / "session.json"
INSTAGRAM_URL = "https://www.instagram.com/"


def _ensure_sessions_dir():
    SESSIONS_DIR.mkdir(exist_ok=True)


def save_cookies(context):
    """Save browser cookies to disk."""
    _ensure_sessions_dir()
    cookies = context.cookies()
    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f)
    print(f"[session] Cookies saved to {COOKIES_FILE}")


def load_cookies(context):
    """Load cookies from disk into browser context. Returns True if loaded."""
    if not COOKIES_FILE.exists():
        return False
    with open(COOKIES_FILE, "r") as f:
        cookies = json.load(f)
    context.add_cookies(cookies)
    print("[session] Cookies loaded from disk.")
    return True


def is_logged_in(page):
    """Check if the current page indicates a logged-in Instagram session."""
    page.goto(INSTAGRAM_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(3000)

    # If redirected to login page, not logged in
    if "/accounts/login" in page.url:
        return False

    # Check for elements only visible when logged in (search icon, profile icon)
    logged_in_selector = "svg[aria-label='Home'], svg[aria-label='Search'], a[href*='/direct/']"
    try:
        page.wait_for_selector(logged_in_selector, timeout=5000)
        return True
    except Exception:
        return False


def wait_for_manual_login(page):
    """Open Instagram login page and wait for user to log in manually."""
    print("\n" + "=" * 60)
    print("MANUAL LOGIN REQUIRED")
    print("=" * 60)
    print("1. The browser will open Instagram's login page.")
    print("2. Log in with your credentials.")
    print("3. Complete any 2FA/verification if prompted.")
    print("4. Once you see your Instagram feed, come back here.")
    print("=" * 60)

    page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")

    # Wait until the URL no longer contains /login (max 5 minutes)
    print("\n[session] Waiting for you to complete login...")
    try:
        page.wait_for_url("**/instagram.com/", timeout=300000)
        page.wait_for_timeout(3000)  # Let the page settle
        print("[session] Login detected!")
        return True
    except Exception:
        print("[session] Login timed out after 5 minutes.")
        return False


def create_browser_session(headless=False):
    """Launch Playwright browser with stealth, load or prompt for login.

    Returns (playwright_instance, browser, context, page).
    Caller is responsible for closing via close_browser_session().
    """
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    stealth_sync(page)

    # Try loading saved cookies
    cookies_loaded = load_cookies(context)

    if cookies_loaded and is_logged_in(page):
        print("[session] Logged in with saved session.")
    else:
        if cookies_loaded:
            print("[session] Saved session expired.")
        success = wait_for_manual_login(page)
        if not success:
            close_browser_session(pw, browser)
            raise RuntimeError("Login failed or timed out.")
        save_cookies(context)

    return pw, browser, context, page


def close_browser_session(pw, browser):
    """Close browser and Playwright instance."""
    try:
        browser.close()
    except Exception:
        pass
    try:
        pw.stop()
    except Exception:
        pass
