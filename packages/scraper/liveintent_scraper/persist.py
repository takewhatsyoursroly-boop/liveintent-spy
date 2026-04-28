from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from liveintent_shared.models import Advertiser, Creative, EmailRaw, Impression

def record_email(session: Session, *, publisher_id: int, imap_uid: int, subject: str | None,
                 from_addr: str | None, raw_html_path: str) -> EmailRaw:
    e = EmailRaw(
        publisher_id=publisher_id, imap_uid=imap_uid, subject=subject,
        from_addr=from_addr, raw_html_path=raw_html_path,
    )
    session.add(e)
    return e

def upsert_advertiser(session: Session, domain: str) -> Advertiser:
    existing = session.scalar(select(Advertiser).where(Advertiser.domain == domain))
    if existing:
        existing.last_seen_at = datetime.now(timezone.utc)
        return existing
    a = Advertiser(domain=domain)
    session.add(a)
    return a

def upsert_creative(session: Session, *, advertiser_id: int, creative_hash: str,
                    screenshot_path: str, click_tracker_url: str) -> Creative:
    existing = session.scalar(select(Creative).where(Creative.creative_hash == creative_hash))
    if existing:
        existing.last_seen_at = datetime.now(timezone.utc)
        return existing
    c = Creative(
        advertiser_id=advertiser_id, creative_hash=creative_hash,
        screenshot_path=screenshot_path, click_tracker_url=click_tracker_url,
    )
    session.add(c)
    return c

def record_impression(session: Session, *, creative_id: int, publisher_id: int, email_id: int) -> Impression:
    i = Impression(creative_id=creative_id, publisher_id=publisher_id, email_id=email_id)
    session.add(i)
    return i
