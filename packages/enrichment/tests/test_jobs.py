import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from liveintent_shared.models import Base, Advertiser, Creative
from liveintent_shared.enums import Vertical, VerticalSource
from liveintent_enrichment.jobs import (
    classify_pending_advertisers, ocr_pending_creatives, cache_pending_creative_images
)

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s

def test_classify_pending_advertisers_skips_manual(db, monkeypatch):
    a_auto = Advertiser(domain="a.com")
    a_manual = Advertiser(
        domain="b.com", vertical=Vertical.FINANCE.value,
        vertical_source=VerticalSource.MANUAL.value, vertical_classified_at=datetime.now(timezone.utc),
    )
    db.add_all([a_auto, a_manual]); db.commit()
    monkeypatch.setattr("liveintent_enrichment.jobs.fetch_landing_text", lambda d: "supps text")
    monkeypatch.setattr("liveintent_enrichment.jobs.classify_landing_page_text", lambda t: "supplements")
    n = classify_pending_advertisers(db, limit=10)
    assert n == 1
    db.refresh(a_auto); db.refresh(a_manual)
    assert a_auto.vertical == "supplements"
    assert a_manual.vertical == "finance"  # untouched

def test_ocr_pending_creatives(db, monkeypatch, tmp_path):
    img = tmp_path / "x.png"; img.write_bytes(b"fake")
    a = Advertiser(domain="a.com"); db.add(a); db.commit()
    c = Creative(advertiser_id=a.id, creative_hash="h", screenshot_path=str(img), click_tracker_url="http://t")
    db.add(c); db.commit()
    monkeypatch.setattr("liveintent_enrichment.jobs.extract_text", lambda p: "BUY NOW")
    n = ocr_pending_creatives(db, limit=10)
    assert n == 1
    db.refresh(c)
    assert c.headline == "BUY NOW"

def test_ocr_skips_already_done(db, monkeypatch):
    a = Advertiser(domain="a.com"); db.add(a); db.commit()
    c = Creative(advertiser_id=a.id, creative_hash="h", screenshot_path="/x", click_tracker_url="http://t", headline="cached")
    db.add(c); db.commit()
    called = []
    monkeypatch.setattr("liveintent_enrichment.jobs.extract_text", lambda p: called.append(p) or "new")
    n = ocr_pending_creatives(db, limit=10)
    assert n == 0
    assert called == []

class _FakeResp:
    def __init__(self, content: bytes, status: int = 200, ct: str = "image/png"):
        self.content = content
        self.status_code = status
        self.headers = {"content-type": ct}

class _FakeClient:
    def __init__(self, mapping):  # mapping: url -> _FakeResp
        self._mapping = mapping
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def get(self, url):
        if url not in self._mapping:
            raise RuntimeError(f"unmocked url {url}")
        return self._mapping[url]

def test_cache_pending_creative_images_caches_and_skips(db, monkeypatch, tmp_path):
    a = Advertiser(domain="a.com"); db.add(a); db.commit()
    real = Creative(advertiser_id=a.id, creative_hash="h1", screenshot_path="", click_tracker_url="http://t1", image_url="https://cdn.example/img.png")
    pixel = Creative(advertiser_id=a.id, creative_hash="h2", screenshot_path="", click_tracker_url="http://t2", image_url="https://sli.x.com/imp?p=1")
    already = Creative(advertiser_id=a.id, creative_hash="h3", screenshot_path="/already/cached.png", click_tracker_url="http://t3", image_url="https://cdn.example/other.png")
    no_url = Creative(advertiser_id=a.id, creative_hash="h4", screenshot_path="", click_tracker_url="http://t4", image_url=None)
    db.add_all([real, pixel, already, no_url]); db.commit()

    big_png = b"\x89PNG\r\n\x1a\n" + b"x" * 4000  # >1KB, valid-looking
    tiny_pixel = b"GIF89a" + b"\x00" * 40         # 1x1 tracker
    fake = _FakeClient({
        "https://cdn.example/img.png": _FakeResp(big_png, ct="image/png"),
        "https://sli.x.com/imp?p=1": _FakeResp(tiny_pixel, ct="image/gif"),
    })
    monkeypatch.setattr("liveintent_enrichment.jobs.httpx.Client", lambda *a, **kw: fake)

    n = cache_pending_creative_images(db, limit=50, data_dir=tmp_path)
    assert n == 1
    db.refresh(real); db.refresh(pixel); db.refresh(already); db.refresh(no_url)
    out = tmp_path / "screenshots" / "cached" / f"{real.id}.png"
    assert out.exists() and out.read_bytes() == big_png
    assert real.screenshot_path == str(out)
    assert pixel.screenshot_path == ""           # tiny → skipped
    assert already.screenshot_path == "/already/cached.png"  # untouched
    assert no_url.screenshot_path == ""          # null image_url → skipped

def test_retry_unresolved_creatives(db, monkeypatch):
    a = Advertiser(domain="a.com"); db.add(a); db.commit()
    c1 = Creative(advertiser_id=a.id, creative_hash="h1", screenshot_path="/x", click_tracker_url="http://t1")
    c2 = Creative(advertiser_id=a.id, creative_hash="h2", screenshot_path="/x", click_tracker_url="http://t2", final_landing_url="https://done.com/x", final_landing_url_resolved_at=datetime.now(timezone.utc))
    db.add_all([c1, c2]); db.commit()
    monkeypatch.setattr("liveintent_scraper.resolve.resolve_final_url", lambda u: "https://newchapter.com/lp")
    monkeypatch.setattr("liveintent_scraper.resolve.extract_advertiser_domain", lambda u: "newchapter.com")
    from liveintent_enrichment.jobs import retry_unresolved_creatives
    n = retry_unresolved_creatives(db, limit=10)
    assert n == 1
    db.refresh(c1); db.refresh(c2)
    assert c1.final_landing_url == "https://newchapter.com/lp"
    assert c2.final_landing_url == "https://done.com/x"  # untouched
