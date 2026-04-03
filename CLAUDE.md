# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && playwright install chromium

# Run pipeline
python scrape.py                                          # defaults from config.yaml
python scrape.py --hashtags "#travel,#adventure"          # override hashtags
python scrape.py --output leads.csv                       # custom output file
python scrape.py --max-profiles 50                        # override limit
python scrape.py --headless                               # headless mode (less safe)
python scrape.py --config /path/to/custom.yaml            # custom config

# Tests
python -m pytest tests/ -v                                # all tests
python -m pytest tests/test_extractor.py -v               # single file
python -m pytest tests/test_writer.py::TestWriteLeadsCsv  # single class
```

## Architecture

Instagram lead generation pipeline: discovers travel creator profiles via hashtag search, scrapes public profile data, extracts contacts, exports to CSV.

**Data flow:**
```
CLI (scrape.py) → Config (src/config.py) → Session (src/session.py) → Hashtag Scanner (src/scanner.py) → Profile Scraper (src/scraper.py) → Data Extractor (src/extractor.py) → CSV Writer (src/writer.py)
```

**Module responsibilities:**
- `src/config.py` — Loads `config.yaml`, merges CLI overrides. Pure function, no side effects.
- `src/session.py` — Playwright browser lifecycle. Cookie persistence in `sessions/session.json`. Manual login on first run, reuses cookies after. Returns `(pw, browser, context, page)` tuple.
- `src/scanner.py` — Visits `instagram.com/explore/tags/{tag}`, collects post links, visits each post to extract author username. Returns `dict[username → source_hashtag]`.
- `src/scraper.py` — Visits profiles with rate limiting (configurable delays, cooldowns, daily cap). Returns `"CHECKPOINT"` sentinel string to signal pipeline stop.
- `src/extractor.py` — Two layers: DOM selectors for profile fields (multiple fallback selectors per field), regex for bio contact extraction (email, phone, WhatsApp, URLs). `parse_follower_count` handles "12.5K"→12500 conversion.
- `src/writer.py` — Deduplicates by username (keeps first occurrence), writes timestamped CSV with 16 columns.

**Key design decisions:**
- Manual login only — no stored passwords, cookies saved to `sessions/` (gitignored)
- `scrape_profile()` returns `dict | "CHECKPOINT" | None` — the string sentinel triggers immediate pipeline stop with data save
- Multiple DOM selectors per field with try/except fallbacks — Instagram's DOM varies
- `check_for_checkpoint()` in `src/scanner.py` is shared by both scanner and scraper modules
- Graceful shutdown on SIGINT saves partial data before exit
- Sequential processing only, no parallelism — simpler rate limiting control

## Anti-Detection

Headful browser by default, `playwright-stealth` plugin, random 2-5s delays between profiles, 30-60s cooldown every 10 profiles, human-like scrolling, daily cap warning at 80 profiles, checkpoint detection with immediate stop. Read-only actions only.

## Profile Data Model

16 CSV columns: `username, display_name, bio, follower_count, following_count, post_count, profile_url, external_link, is_verified, account_category, email, phone, whatsapp_link, bio_urls, scraped_at, source_hashtag`

## Testing

Unit tests cover config loading, regex/bio extraction, follower count parsing, CSV writing, and deduplication. Browser-dependent modules (session, scanner, scraper) are tested manually against real Instagram — no mocks for DOM interaction.
