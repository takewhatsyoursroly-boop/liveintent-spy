import pytest
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from liveintent_shared.models import Base, Publisher, Impression, Advertiser
from liveintent_scraper.main import process_email
from liveintent_scraper.render import browser_context

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.mark.asyncio
async def test_pipeline_records_impression(monkeypatch, tmp_path):
    # Use shared in-process DB, monkeypatch session_scope
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    p = Publisher(domain="morningbrew.com", from_address="news@morningbrew.com")
    with Session(engine) as s:
        s.add(p); s.commit(); pub_id = p.id

    from contextlib import contextmanager
    @contextmanager
    def fake_session_scope():
        s = Session(engine)
        try:
            yield s; s.commit()
        finally:
            s.close()
    monkeypatch.setattr("liveintent_scraper.main.session_scope", fake_session_scope)

    # Stub the URL resolver so we don't hit network
    monkeypatch.setattr("liveintent_scraper.main.resolve_final_url", lambda u: "https://newchapter.com/lp")

    raw = (FIXTURES / "test.eml").read_bytes()
    async with browser_context() as browser:
        await process_email(browser, raw, uid=42, data_dir=tmp_path)

    with Session(engine) as s:
        imps = s.scalars(select(Impression)).all()
        ads = s.scalars(select(Advertiser)).all()
        assert len(imps) == 1
        assert len(ads) == 1
        assert ads[0].domain == "newchapter.com"
