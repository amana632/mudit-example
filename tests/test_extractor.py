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
