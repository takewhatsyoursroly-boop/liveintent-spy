import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from liveintent_shared.models import Base, Publisher, Advertiser, Creative, Impression, EmailRaw
from liveintent_shared.enums import Vertical

@pytest.fixture
def db_with_impressions():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    s = Session(engine)
    p = Publisher(domain="p.com", seed_email_address="p@x.com")
    s.add(p); s.flush()
    e = EmailRaw(publisher_id=p.id, imap_uid=1, raw_html_path="/x")
    s.add(e); s.flush()
    advs = []
    # 3 supplements advertisers, varying impression counts
    for i, (dom, vert, count) in enumerate([
        ("a1.com", Vertical.SUPPLEMENTS.value, 10),
        ("a2.com", Vertical.SUPPLEMENTS.value, 5),
        ("a3.com", Vertical.FINANCE.value, 8),
        ("a4.com", Vertical.UNCLASSIFIED.value, 1),
    ]):
        a = Advertiser(domain=dom, vertical=vert)
        s.add(a); s.flush()
        c = Creative(advertiser_id=a.id, creative_hash=f"h{i}", screenshot_path="/s", click_tracker_url="http://t")
        s.add(c); s.flush()
        for _ in range(count):
            s.add(Impression(creative_id=c.id, publisher_id=p.id, email_id=e.id))
        advs.append(a)
    s.commit()
    yield s
    s.close()
