import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from liveintent_shared.models import Base, Publisher, Advertiser, Creative, Impression, EmailRaw

@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/t.db")
    monkeypatch.setenv("ADMIN_TOKEN", "tok")
    monkeypatch.setenv("IMAP_HOST", "x"); monkeypatch.setenv("IMAP_USER", "x"); monkeypatch.setenv("IMAP_PASS", "x")
    # Reset cached engine/session
    import liveintent_shared.db as db
    db._engine = None; db._Session = None
    engine = db.get_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        p = Publisher(domain="p.com", seed_email_address="p@x.com"); s.add(p); s.flush()
        a = Advertiser(domain="a.com", vertical="supplements"); s.add(a); s.flush()
        e = EmailRaw(publisher_id=p.id, imap_uid=1, raw_html_path="/x"); s.add(e); s.flush()
        c = Creative(advertiser_id=a.id, creative_hash="h", screenshot_path="/x", click_tracker_url="http://t"); s.add(c); s.flush()
        s.add(Impression(creative_id=c.id, publisher_id=p.id, email_id=e.id))
        s.commit()
    from liveintent_api.main import app
    return TestClient(app)

H = {"Authorization": "Bearer tok"}

def test_list_advertisers(client):
    r = client.get("/advertisers", headers=H)
    assert r.status_code == 200
    body = r.json()
    assert any(row["domain"] == "a.com" for row in body)

def test_advertiser_detail(client):
    r = client.get("/advertisers/a.com", headers=H)
    assert r.status_code == 200
    assert r.json()["vertical"] == "supplements"

def test_advertiser_detail_404(client):
    r = client.get("/advertisers/nonexistent.com", headers=H)
    assert r.status_code == 404

def test_list_publishers(client):
    r = client.get("/publishers", headers=H)
    assert r.status_code == 200
    assert any(p["domain"] == "p.com" for p in r.json())

def test_publisher_detail(client):
    r = client.get("/publishers/p.com", headers=H)
    assert r.status_code == 200
    assert r.json()["top_advertisers"][0]["domain"] == "a.com"
