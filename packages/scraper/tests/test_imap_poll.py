from pathlib import Path
from liveintent_scraper.imap_poll import parse_email_bytes, route_email_to_publisher

FIXTURES = Path(__file__).parent / "fixtures"

def test_parse_email_extracts_html_and_to():
    raw = (FIXTURES / "test.eml").read_bytes()
    parsed = parse_email_bytes(raw)
    assert parsed.to_addr == "r.alvarez@yourdomain.com"
    assert parsed.from_addr == "news@morningbrew.com"
    assert parsed.subject == "Test newsletter"
    assert "track.liveintent.com" in parsed.html_body

def test_route_email_to_publisher_known(db_session):
    from liveintent_shared.models import Publisher
    p = Publisher(domain="morningbrew.com", seed_email_address="r.alvarez@yourdomain.com")
    db_session.add(p); db_session.flush()
    matched = route_email_to_publisher(db_session, "r.alvarez@yourdomain.com")
    assert matched is not None
    assert matched.id == p.id

def test_route_email_to_publisher_unknown(db_session):
    matched = route_email_to_publisher(db_session, "stranger@somewhere.com")
    assert matched is None
