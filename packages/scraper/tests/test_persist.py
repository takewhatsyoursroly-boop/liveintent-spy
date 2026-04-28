from datetime import datetime, timezone
from liveintent_shared.models import Publisher, Advertiser, Creative, Impression, EmailRaw
from liveintent_scraper.persist import (
    upsert_advertiser, upsert_creative, record_impression, record_email
)

def test_record_email_creates_row(db_session):
    p = Publisher(domain="x.com", seed_email_address="x@x.com")
    db_session.add(p); db_session.flush()
    e = record_email(db_session, publisher_id=p.id, imap_uid=42, subject="s", from_addr="f", raw_html_path="/x.html")
    db_session.flush()
    assert e.id is not None
    assert e.imap_uid == 42

def test_upsert_advertiser_creates_then_updates(db_session):
    a1 = upsert_advertiser(db_session, "newchapter.com")
    db_session.flush()
    a2 = upsert_advertiser(db_session, "newchapter.com")
    db_session.flush()
    assert a1.id == a2.id

def test_upsert_creative_dedupes_by_hash(db_session):
    a = upsert_advertiser(db_session, "x.com"); db_session.flush()
    c1 = upsert_creative(db_session, advertiser_id=a.id, creative_hash="abc", screenshot_path="/p1", click_tracker_url="http://t1")
    db_session.flush()
    c2 = upsert_creative(db_session, advertiser_id=a.id, creative_hash="abc", screenshot_path="/p2", click_tracker_url="http://t2")
    db_session.flush()
    assert c1.id == c2.id
    # First insert wins on path/url
    assert c2.screenshot_path == "/p1"

def test_record_impression(db_session):
    p = Publisher(domain="p.com", seed_email_address="p@x.com"); db_session.add(p)
    a = upsert_advertiser(db_session, "a.com"); db_session.flush()
    e = record_email(db_session, publisher_id=p.id, imap_uid=1, subject="s", from_addr="f", raw_html_path="/x")
    c = upsert_creative(db_session, advertiser_id=a.id, creative_hash="h", screenshot_path="/s", click_tracker_url="http://t")
    db_session.flush()
    imp = record_impression(db_session, creative_id=c.id, publisher_id=p.id, email_id=e.id)
    db_session.flush()
    assert imp.id is not None
