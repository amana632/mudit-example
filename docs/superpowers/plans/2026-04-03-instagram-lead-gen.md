# Instagram Lead Generation Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool that discovers travel creator Instagram profiles via hashtag search, scrapes their profile data, and exports leads to CSV.

**Architecture:** Playwright browser automation with cookie-based session persistence. Pipeline flows: config loading → session restore/login → hashtag page scanning for usernames → profile visiting and data extraction → CSV export. All browser interactions include human-like delays and stealth measures.

**Tech Stack:** Python 3.10+, Playwright, playwright-stealth, PyYAML, argparse, pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `requirements.txt` | Python dependencies |
| `config.yaml` | Default hashtags, rate limits, output settings |
| `.gitignore` | Ignore sessions/, output/, venv/ |
| `scrape.py` | CLI entry point — arg parsing, orchestration |
| `src/__init__.py` | Package marker |
| `src/config.py` | Load and merge config.yaml with CLI overrides |
| `src/session.py` | Playwright browser launch, cookie save/load, login flow |
| `src/scanner.py` | Visit hashtag pages, collect unique usernames from posts |
| `src/scraper.py` | Visit profile pages with human-like behavior, detect checkpoints |
| `src/extractor.py` | Parse DOM elements + regex extract contacts from bio text |
| `src/writer.py` | Deduplicate profiles, write timestamped CSV |
| `tests/__init__.py` | Test package marker |
| `tests/test_config.py` | Config loading tests |
| `tests/test_extractor.py` | Bio parsing and regex extraction tests |
| `tests/test_writer.py` | CSV writing and deduplication tests |

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `config.yaml`
- Create: `.gitignore`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
playwright==1.52.0
playwright-stealth==1.0.6
pyyaml==6.0.2
pytest==8.3.4
```

- [ ] **Step 2: Create config.yaml**

```yaml
hashtags:
  - "#travelcreator"
  - "#grouptrips"
  - "#hostedtrips"
  - "#travelwithme"
  - "#triporganizer"

settings:
  max_profiles_per_run: 30
  max_posts_per_hashtag: 50
  delay_between_profiles: [2, 5]
  cooldown_every: 10
  cooldown_duration: [30, 60]
  daily_cap_warning: 80
  headless: false

output:
  directory: "./output"
  filename_prefix: "leads"
```

- [ ] **Step 3: Create .gitignore**

```
sessions/
output/
__pycache__/
*.pyc
venv/
.venv/
```

- [ ] **Step 4: Create empty __init__.py files**

Create `src/__init__.py` and `tests/__init__.py` as empty files.

- [ ] **Step 5: Set up virtual environment and install dependencies**

Run:
```bash
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && playwright install chromium
```
Expected: All packages install successfully, Chromium browser downloaded.

- [ ] **Step 6: Create output and sessions directories**

Run:
```bash
mkdir -p output sessions
```

- [ ] **Step 7: Commit**

```bash
git add requirements.txt config.yaml .gitignore src/__init__.py tests/__init__.py
git commit -m "chore: scaffold project structure and dependencies"
```

---

### Task 2: Config Loader

**Files:**
- Create: `src/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests for config loader**

```python
# tests/test_config.py
import os
import tempfile
import pytest
from src.config import load_config


def test_load_config_from_file():
    yaml_content = """
hashtags:
  - "#travel"
  - "#adventure"

settings:
  max_profiles_per_run: 20
  max_posts_per_hashtag: 40
  delay_between_profiles: [1, 3]
  cooldown_every: 5
  cooldown_duration: [10, 20]
  daily_cap_warning: 50
  headless: true

output:
  directory: "./out"
  filename_prefix: "test"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        f.flush()
        config = load_config(config_path=f.name)

    assert config["hashtags"] == ["#travel", "#adventure"]
    assert config["settings"]["max_profiles_per_run"] == 20
    assert config["settings"]["headless"] is True
    assert config["output"]["directory"] == "./out"
    os.unlink(f.name)


def test_load_config_with_cli_overrides():
    yaml_content = """
hashtags:
  - "#travel"

settings:
  max_profiles_per_run: 30
  max_posts_per_hashtag: 50
  delay_between_profiles: [2, 5]
  cooldown_every: 10
  cooldown_duration: [30, 60]
  daily_cap_warning: 80
  headless: false

output:
  directory: "./output"
  filename_prefix: "leads"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        f.flush()
        overrides = {
            "hashtags": ["#beach", "#surf"],
            "output_file": "custom.csv",
            "max_profiles": 10,
            "headless": True,
        }
        config = load_config(config_path=f.name, overrides=overrides)

    assert config["hashtags"] == ["#beach", "#surf"]
    assert config["output"]["custom_output_file"] == "custom.csv"
    assert config["settings"]["max_profiles_per_run"] == 10
    assert config["settings"]["headless"] is True
    os.unlink(f.name)


def test_load_config_default_path(monkeypatch):
    """When no path given, loads from config.yaml in project root."""
    config = load_config()
    assert "#travelcreator" in config["hashtags"]
    assert config["settings"]["max_profiles_per_run"] == 30
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.config'`

- [ ] **Step 3: Implement config loader**

```python
# src/config.py
from pathlib import Path
import yaml


def load_config(config_path=None, overrides=None):
    """Load config from YAML file and apply CLI overrides."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if overrides:
        if overrides.get("hashtags"):
            config["hashtags"] = overrides["hashtags"]
        if overrides.get("output_file"):
            config["output"]["custom_output_file"] = overrides["output_file"]
        if overrides.get("max_profiles") is not None:
            config["settings"]["max_profiles_per_run"] = overrides["max_profiles"]
        if overrides.get("headless") is not None:
            config["settings"]["headless"] = overrides["headless"]

    return config
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_config.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/config.py tests/test_config.py
git commit -m "feat: add config loader with YAML parsing and CLI overrides"
```

---

### Task 3: Data Extractor

**Files:**
- Create: `src/extractor.py`
- Create: `tests/test_extractor.py`

- [ ] **Step 1: Write failing tests for bio text extraction**

```python
# tests/test_extractor.py
import pytest
from src.extractor import extract_contacts_from_bio, parse_follower_count


class TestExtractContactsFromBio:
    def test_extract_email(self):
        bio = "Travel blogger | contact@travelwithme.com | DM for collabs"
        result = extract_contacts_from_bio(bio)
        assert result["email"] == "contact@travelwithme.com"

    def test_extract_multiple_emails_takes_first(self):
        bio = "hello@trip.com and backup@trip.com"
        result = extract_contacts_from_bio(bio)
        assert result["email"] == "hello@trip.com"

    def test_extract_phone(self):
        bio = "Book now: +91 98765 43210"
        result = extract_contacts_from_bio(bio)
        assert result["phone"] == "+91 98765 43210"

    def test_extract_whatsapp_wa_me(self):
        bio = "WhatsApp: wa.me/919876543210"
        result = extract_contacts_from_bio(bio)
        assert result["whatsapp_link"] == "wa.me/919876543210"

    def test_extract_whatsapp_api(self):
        bio = "Chat: api.whatsapp.com/send?phone=919876543210"
        result = extract_contacts_from_bio(bio)
        assert result["whatsapp_link"] == "api.whatsapp.com/send?phone=919876543210"

    def test_extract_urls(self):
        bio = "Check https://mytrips.com and http://blog.travel.com/tours"
        result = extract_contacts_from_bio(bio)
        assert "https://mytrips.com" in result["bio_urls"]
        assert "http://blog.travel.com/tours" in result["bio_urls"]

    def test_no_contacts(self):
        bio = "Just a travel lover exploring the world"
        result = extract_contacts_from_bio(bio)
        assert result["email"] is None
        assert result["phone"] is None
        assert result["whatsapp_link"] is None
        assert result["bio_urls"] == []

    def test_empty_bio(self):
        result = extract_contacts_from_bio("")
        assert result["email"] is None
        assert result["phone"] is None
        assert result["whatsapp_link"] is None
        assert result["bio_urls"] == []

    def test_none_bio(self):
        result = extract_contacts_from_bio(None)
        assert result["email"] is None


class TestParseFollowerCount:
    def test_plain_number(self):
        assert parse_follower_count("1,234") == 1234

    def test_k_suffix(self):
        assert parse_follower_count("12.5K") == 12500

    def test_m_suffix(self):
        assert parse_follower_count("1.2M") == 1200000

    def test_plain_small(self):
        assert parse_follower_count("500") == 500

    def test_none(self):
        assert parse_follower_count(None) == 0

    def test_empty(self):
        assert parse_follower_count("") == 0

    def test_followers_word(self):
        assert parse_follower_count("12.5K followers") == 12500
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_extractor.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.extractor'`

- [ ] **Step 3: Implement extractor**

```python
# src/extractor.py
import re


def extract_contacts_from_bio(bio):
    """Extract email, phone, WhatsApp link, and URLs from bio text."""
    result = {
        "email": None,
        "phone": None,
        "whatsapp_link": None,
        "bio_urls": [],
    }

    if not bio:
        return result

    # Email
    email_match = re.search(r'[\w.\-+]+@[\w.\-]+\.\w+', bio)
    if email_match:
        result["email"] = email_match.group(0)

    # WhatsApp (check before generic URLs so we can separate them)
    wa_match = re.search(r'(?:wa\.me/[\w\d+]+|api\.whatsapp\.com/send\?phone=[\w\d+]+)', bio)
    if wa_match:
        result["whatsapp_link"] = wa_match.group(0)

    # Phone number (international format)
    phone_match = re.search(r'[\+]?[\d][\d\s\-\(\)]{6,14}[\d]', bio)
    if phone_match:
        result["phone"] = phone_match.group(0)

    # URLs (exclude WhatsApp links already captured)
    url_matches = re.findall(r'https?://[^\s,\)\"\']+', bio)
    for url in url_matches:
        if "wa.me" not in url and "whatsapp.com" not in url:
            result["bio_urls"].append(url)

    return result


def parse_follower_count(text):
    """Parse follower count strings like '12.5K', '1.2M', '1,234' into integers."""
    if not text:
        return 0

    text = text.strip().upper().replace(",", "")

    # Remove trailing words like "FOLLOWERS"
    text = re.sub(r'\s*(FOLLOWERS|FOLLOWING|POSTS).*', '', text)

    multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}

    for suffix, mult in multipliers.items():
        if text.endswith(suffix):
            number = float(text[:-1])
            return int(number * mult)

    try:
        return int(float(text))
    except ValueError:
        return 0


def extract_profile_data(page):
    """Extract all profile fields from a Playwright page object.

    Expects the page to be on an Instagram profile (instagram.com/username).
    Returns a dict with all profile fields.
    """
    data = {}

    # Username from URL
    url_path = page.url.rstrip("/").split("/")[-1]
    data["username"] = url_path

    # Display name
    try:
        name_el = page.query_selector("header section h2, header section span[class*='x1lliihq']")
        if not name_el:
            name_el = page.query_selector("header h1")
        data["display_name"] = name_el.inner_text().strip() if name_el else ""
    except Exception:
        data["display_name"] = ""

    # Bio
    try:
        bio_el = page.query_selector("header section div[class*='x7a106z'] span, header section div.-vDIg span")
        if not bio_el:
            bio_el = page.query_selector("div[class*='x7a106z'] span[class*='x1lliihq']")
        data["bio"] = bio_el.inner_text().strip() if bio_el else ""
    except Exception:
        data["bio"] = ""

    # Stats (followers, following, posts)
    try:
        stat_elements = page.query_selector_all("header section ul li span span, header section ul li a span span")
        stats = []
        for el in stat_elements:
            title = el.get_attribute("title")
            text = title if title else el.inner_text()
            stats.append(text)

        data["post_count"] = parse_follower_count(stats[0]) if len(stats) > 0 else 0
        data["follower_count"] = parse_follower_count(stats[1]) if len(stats) > 1 else 0
        data["following_count"] = parse_follower_count(stats[2]) if len(stats) > 2 else 0
    except Exception:
        data["post_count"] = 0
        data["follower_count"] = 0
        data["following_count"] = 0

    # Profile URL
    data["profile_url"] = f"https://www.instagram.com/{data['username']}/"

    # External link
    try:
        link_el = page.query_selector("header section a[rel='me nofollow noopener noreferrer'], header section div[class*='x7a106z'] a[href*='l.instagram.com']")
        if not link_el:
            link_el = page.query_selector("a[class*='xjbqb8w'][target='_blank']")
        data["external_link"] = link_el.get_attribute("href") if link_el else ""
    except Exception:
        data["external_link"] = ""

    # Verified badge
    try:
        verified_el = page.query_selector("header section span[title='Verified'], header section svg[aria-label='Verified']")
        data["is_verified"] = verified_el is not None
    except Exception:
        data["is_verified"] = False

    # Account category (business/creator label)
    try:
        cat_el = page.query_selector("header section div[class*='x1ep9csh'], header section div.JEQJK")
        data["account_category"] = cat_el.inner_text().strip() if cat_el else ""
    except Exception:
        data["account_category"] = ""

    # Extract contacts from bio
    contacts = extract_contacts_from_bio(data["bio"])
    data["email"] = contacts["email"]
    data["phone"] = contacts["phone"]
    data["whatsapp_link"] = contacts["whatsapp_link"]
    data["bio_urls"] = "; ".join(contacts["bio_urls"])

    return data
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_extractor.py -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add src/extractor.py tests/test_extractor.py
git commit -m "feat: add data extractor with bio regex parsing and follower count parser"
```

---

### Task 4: CSV Writer

**Files:**
- Create: `src/writer.py`
- Create: `tests/test_writer.py`

- [ ] **Step 1: Write failing tests for CSV writer**

```python
# tests/test_writer.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_writer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.writer'`

- [ ] **Step 3: Implement CSV writer**

```python
# src/writer.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_writer.py -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add src/writer.py tests/test_writer.py
git commit -m "feat: add CSV writer with deduplication and timestamped output"
```

---

### Task 5: Session Manager

**Files:**
- Create: `src/session.py`

- [ ] **Step 1: Implement session manager**

```python
# src/session.py
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
```

- [ ] **Step 2: Manual smoke test**

Run:
```bash
python -c "from src.session import create_browser_session, close_browser_session; pw, br, ctx, pg = create_browser_session(headless=False); print('Logged in as:', pg.url); close_browser_session(pw, br)"
```
Expected: Browser opens, prompts for login (first run) or reuses session. Prints the URL after login.

- [ ] **Step 3: Commit**

```bash
git add src/session.py
git commit -m "feat: add session manager with cookie persistence and manual login flow"
```

---

### Task 6: Hashtag Scanner

**Files:**
- Create: `src/scanner.py`

- [ ] **Step 1: Implement hashtag scanner**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/scanner.py
git commit -m "feat: add hashtag scanner with post-to-username extraction"
```

---

### Task 7: Profile Scraper

**Files:**
- Create: `src/scraper.py`

- [ ] **Step 1: Implement profile scraper**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/scraper.py
git commit -m "feat: add profile scraper with human-like behavior and checkpoint detection"
```

---

### Task 8: CLI Entry Point

**Files:**
- Create: `scrape.py`

- [ ] **Step 1: Implement CLI entry point**

```python
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
```

- [ ] **Step 2: Verify CLI help works**

Run: `python scrape.py --help`
Expected: Shows usage info with all arguments

- [ ] **Step 3: Commit**

```bash
git add scrape.py
git commit -m "feat: add CLI entry point with arg parsing and graceful shutdown"
```

---

### Task 9: Run All Tests and Integration Test

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All unit tests pass

- [ ] **Step 2: Manual end-to-end test**

Run: `python scrape.py --max-profiles 3`

Expected flow:
1. Browser opens
2. If first run: Instagram login page appears, user logs in manually
3. Scans default hashtags
4. Visits up to 3 profiles
5. CSV created in `output/` directory
6. Browser closes

Verify:
- CSV file exists with correct headers and data
- `sessions/session.json` saved
- No errors in console

- [ ] **Step 3: Test with custom hashtags**

Run: `python scrape.py --hashtags "#travelcreator" --max-profiles 2`

Expected: Only scans the one hashtag, scrapes 2 profiles max.

- [ ] **Step 4: Test Ctrl+C graceful shutdown**

Run `python scrape.py` and press Ctrl+C mid-scrape.
Expected: "Saving collected data..." message, partial CSV saved.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete Instagram lead generation pipeline v1"
```
