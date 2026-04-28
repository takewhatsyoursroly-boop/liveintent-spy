import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from liveintent_shared.models import Base, Publisher, Advertiser, Creative, Impression, EmailRaw, DigestRun
from liveintent_shared.enums import Vertical, VerticalSource

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s

def test_publisher_creation(db):
    p = Publisher(domain="morningbrew.com", name="Morning Brew", seed_email_address="mb@x.com")
    db.add(p); db.flush()
    assert p.id is not None
    assert p.active is True

def test_advertiser_defaults(db):
    a = Advertiser(domain="newchapter.com")
    db.add(a); db.flush()
    assert a.vertical == Vertical.UNCLASSIFIED
    assert a.vertical_source == VerticalSource.AUTO

def test_creative_unique_hash(db):
    a = Advertiser(domain="x.com"); db.add(a); db.flush()
    c1 = Creative(advertiser_id=a.id, creative_hash="abc123", screenshot_path="/x", click_tracker_url="http://x")
    db.add(c1); db.flush()
    c2 = Creative(advertiser_id=a.id, creative_hash="abc123", screenshot_path="/y", click_tracker_url="http://y")
    db.add(c2)
    with pytest.raises(Exception):
        db.flush()

def test_impression_relations(db):
    p = Publisher(domain="p.com", seed_email_address="p@x.com"); db.add(p)
    a = Advertiser(domain="a.com"); db.add(a); db.flush()
    e = EmailRaw(publisher_id=p.id, imap_uid=1, subject="s", from_addr="x", raw_html_path="/x"); db.add(e)
    c = Creative(advertiser_id=a.id, creative_hash="h", screenshot_path="/s", click_tracker_url="http://t"); db.add(c); db.flush()
    i = Impression(creative_id=c.id, publisher_id=p.id, email_id=e.id); db.add(i); db.flush()
    assert i.id is not None
