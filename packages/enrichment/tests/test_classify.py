import pytest
from liveintent_enrichment.classify import classify_landing_page_text, VALID_VERTICALS

def test_classify_returns_one_of_valid_verticals(monkeypatch):
    monkeypatch.setattr(
        "liveintent_enrichment.classify._call_claude",
        lambda prompt: "supplements"
    )
    result = classify_landing_page_text("Buy our amazing fish oil capsules")
    assert result == "supplements"

def test_classify_falls_back_to_other_on_invalid_response(monkeypatch):
    monkeypatch.setattr(
        "liveintent_enrichment.classify._call_claude",
        lambda prompt: "completely unknown category"
    )
    result = classify_landing_page_text("text")
    assert result == "other"

def test_classify_returns_unclassified_on_error(monkeypatch):
    def boom(prompt): raise RuntimeError("api down")
    monkeypatch.setattr("liveintent_enrichment.classify._call_claude", boom)
    result = classify_landing_page_text("text")
    assert result == "unclassified"

def test_valid_verticals_match_enum():
    from liveintent_shared.enums import Vertical
    expected = {v.value for v in Vertical if v.value not in ("unclassified",)}
    assert expected == set(VALID_VERTICALS)
