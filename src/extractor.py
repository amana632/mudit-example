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
