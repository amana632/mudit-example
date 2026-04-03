# Instagram Lead Generation Pipeline — Design Spec

## Overview

A Python CLI tool that scrapes Instagram profiles of travel creators and travel companies via hashtag discovery, extracts contact/lead data, and outputs to CSV. Designed for small-batch on-demand use (<100 profiles) with anti-detection safeguards.

## Goals

- Discover travel creator/company profiles by scanning configurable hashtag pages
- Extract: username, display name, bio, follower count, external link, email, phone, WhatsApp, and other contact info from profile bio
- Output deduplicated leads to timestamped CSV
- Protect the user's Instagram account from bans/restrictions

## Non-Goals

- Linktree/link-in-bio page crawling (only direct profile data)
- Follower threshold filtering
- Scheduled/automated runs
- CRM integration
- Following, liking, or commenting on profiles

## Architecture

```
[CLI Entry] → [Config Loader] → [Session Manager] → [Hashtag Scanner] → [Profile Scraper] → [Data Extractor] → [CSV Writer]
```

### Components

1. **CLI Entry (`scrape.py`)** — Parses CLI args, loads config, orchestrates pipeline
2. **Config (`config.yaml`)** — Hashtags, delay settings, limits, output preferences
3. **Session Manager (`src/session.py`)** — Handles Instagram login via headful Playwright browser. Saves cookies to `sessions/` on first login. Reuses cookies on subsequent runs. Prompts for re-login if session expires. Never stores passwords.
4. **Hashtag Scanner (`src/scanner.py`)** — Navigates to `instagram.com/explore/tags/{hashtag}`. Scrolls "Recent" posts section. Collects unique profile usernames from post overlays/links. Respects `max_posts_per_hashtag` config limit.
5. **Profile Scraper (`src/scraper.py`)** — Visits each profile URL. Waits for page load. Implements human-like delays and scrolling. Detects checkpoint/challenge screens and exits gracefully.
6. **Data Extractor (`src/extractor.py`)** — Parses DOM for profile fields. Regex extraction from bio text for email, phone, WhatsApp, URLs.
7. **CSV Writer (`src/writer.py`)** — Deduplicates by username. Writes timestamped CSV to output directory.

### CLI Interface

```bash
python scrape.py                                          # defaults from config.yaml
python scrape.py --hashtags "#travelcreator,#grouptrips"  # override hashtags
python scrape.py --output leads.csv                       # custom output file
python scrape.py --max-profiles 50                        # override max profiles
python scrape.py --headless                               # run headless (less safe)
```

## Data Model

### Profile Fields (from DOM)

| Field | Source | Method |
|-------|--------|--------|
| username | Profile page URL/header | Parse from page |
| display_name | Profile name element | DOM selector |
| bio | Bio section | DOM selector |
| follower_count | Stats section | DOM selector, parse "12.5K" to number |
| following_count | Stats section | DOM selector |
| post_count | Stats section | DOM selector |
| profile_url | Constructed | `instagram.com/{username}` |
| external_link | Bio link button | DOM selector |
| is_verified | Verified badge | Badge element check |
| account_category | Account label | Category label text (e.g., "Travel Agency") |

### Extracted Fields (regex from bio text)

| Field | Pattern |
|-------|---------|
| email | Standard email regex `[\w.-]+@[\w.-]+\.\w+` |
| phone | International/local phone patterns `[\+]?[\d\s\-\(\)]{7,15}` |
| whatsapp_link | `wa.me/*` or `api.whatsapp.com/*` |
| bio_urls | Any `http(s)://` URLs in bio text |

### CSV Output Columns

```
username, display_name, bio, follower_count, following_count, post_count, profile_url, external_link, is_verified, account_category, email, phone, whatsapp_link, bio_urls, scraped_at, source_hashtag
```

## Anti-Detection Strategy

### Session Persistence
- First run: user logs in manually in visible Playwright browser, cookies saved to `sessions/session.json`
- Subsequent runs: cookies loaded automatically, no re-login needed
- Session expiry detected and user prompted to re-login
- No passwords stored anywhere in code or config

### Human-like Behavior
- Random delay between profile visits: 2-5 seconds
- Cooldown pause every 10 profiles: 30-60 seconds
- Random scroll actions on profile pages before extracting
- Realistic viewport (1280x720) and user-agent

### Rate Limiting
- Default max 30 profiles per run (configurable)
- Max 50 posts scanned per hashtag page
- Daily cap warning at 80 profiles
- All limits configurable in `config.yaml`

### Stealth
- Headful mode by default (visible browser)
- `playwright-stealth` plugin to mask WebDriver fingerprints
- Sequential requests only, no parallelism
- Read-only actions — never follows/likes/comments

### Checkpoint Handling
- If Instagram shows a challenge/checkpoint screen, the tool stops immediately
- Warns the user and saves any data collected so far
- Does not attempt to solve challenges programmatically

## Config File

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

## Project Structure

```
mudit-example/
├── scrape.py              # CLI entry point
├── config.yaml            # Hashtags, delays, limits, output settings
├── requirements.txt       # Python dependencies
├── src/
│   ├── __init__.py
│   ├── session.py         # Login & cookie management
│   ├── scanner.py         # Hashtag page -> collect usernames
│   ├── scraper.py         # Visit profiles -> raw page data
│   ├── extractor.py       # Parse profile data + regex extraction
│   └── writer.py          # Dedup + CSV output
├── output/                # Generated CSVs (gitignored)
└── sessions/              # Saved cookie files (gitignored)
```

## Dependencies

- `playwright` — browser automation
- `playwright-stealth` — anti-detection
- `pyyaml` — config parsing
- Standard library: `argparse`, `re`, `csv`, `json`, `datetime`, `random`, `pathlib`

## Error Handling

- **Network errors**: Retry once after 10s delay, then skip profile and log warning
- **Profile not found (404)**: Skip, log to console
- **Private profile**: Skip, log as "private" in output
- **Checkpoint/challenge**: Stop entire run, save collected data, warn user
- **Session expired**: Prompt user to re-login in headful browser
- **Keyboard interrupt (Ctrl+C)**: Save any data collected so far before exiting

## Testing Strategy

- Manual testing against real Instagram (no mock — Instagram's DOM is the contract)
- Test regex extraction with sample bio strings (unit testable)
- Test CSV writer with mock data (unit testable)
- Test config loading with various yaml inputs (unit testable)
