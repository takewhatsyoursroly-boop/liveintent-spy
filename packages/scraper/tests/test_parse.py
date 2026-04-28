from pathlib import Path
from liveintent_scraper.parse import find_ad_slots

FIXTURES = Path(__file__).parent / "fixtures"

def _load(name: str) -> str:
    return (FIXTURES / name).read_text()

def test_one_slot():
    slots = find_ad_slots(_load("sample_email_one_slot.html"))
    assert len(slots) == 1
    assert slots[0].slot_index == 0
    assert "track.liveintent.com" in slots[0].click_tracker_url
    assert slots[0].image_src == "https://cdn.liveintent.com/creative/img1.jpg"

def test_no_slots():
    slots = find_ad_slots(_load("sample_email_no_slots.html"))
    assert slots == []

def test_multiple_slots_indexed_in_order():
    slots = find_ad_slots(_load("sample_email_multi_slot.html"))
    assert len(slots) == 2
    assert [s.slot_index for s in slots] == [0, 1]
    assert "advertiser1" in slots[0].click_tracker_url
    assert "advertiser2" in slots[1].click_tracker_url

def test_slot_records_selector_used():
    slots = find_ad_slots(_load("sample_email_one_slot.html"))
    assert slots[0].selector_used in (
        'a[href*="li/r/"]',
        'a[href*="track.liveintent.com"]',
        'a[href*="liveintent.com/r/"]',
    )
