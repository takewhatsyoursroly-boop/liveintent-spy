from pathlib import Path
from liveintent_enrichment.ocr import extract_text

FIX = Path(__file__).parent / "fixtures"

def test_extract_text_from_simple_image():
    text = extract_text(FIX / "sample_creative.png")
    assert text is not None
    assert "fish" in text.lower() or "oil" in text.lower()

def test_extract_text_returns_none_for_missing_file(tmp_path):
    assert extract_text(tmp_path / "nonexistent.png") is None
