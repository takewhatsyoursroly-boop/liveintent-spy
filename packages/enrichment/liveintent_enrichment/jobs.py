from datetime import datetime, timezone
from pathlib import Path
import httpx
import structlog
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session
from liveintent_shared.models import Advertiser, Creative
from liveintent_shared.enums import Vertical, VerticalSource
from .classify import classify_landing_page_text
from .ocr import extract_text

log = structlog.get_logger(__name__)

def fetch_landing_text(domain: str, *, timeout: float = 10.0) -> str | None:
    url = f"https://{domain}/"
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 LiveIntentSpyBot/0.1"}) as c:
            r = c.get(url)
            if r.status_code >= 400:
                return None
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return " ".join(soup.get_text(separator=" ", strip=True).split())
    except Exception as e:
        log.warning("enrich.fetch_failed", domain=domain, error=str(e))
        return None

def classify_pending_advertisers(session: Session, *, limit: int = 50) -> int:
    """Classify advertisers where vertical_classified_at IS NULL.
    Never overwrites manual classifications. Returns count processed."""
    pending = session.scalars(
        select(Advertiser)
        .where(Advertiser.vertical_classified_at.is_(None))
        .where(Advertiser.vertical_source == VerticalSource.AUTO.value)
        .limit(limit)
    ).all()
    n = 0
    for a in pending:
        text = fetch_landing_text(a.domain)
        if text is None:
            log.info("enrich.classify_no_text", domain=a.domain)
            continue
        a.vertical = classify_landing_page_text(text)
        a.vertical_classified_at = datetime.now(timezone.utc)
        session.flush()
        n += 1
    return n

def ocr_pending_creatives(session: Session, *, limit: int = 50) -> int:
    """OCR creatives whose headline is NULL. Returns count processed."""
    pending = session.scalars(
        select(Creative).where(Creative.headline.is_(None)).limit(limit)
    ).all()
    n = 0
    for c in pending:
        text = extract_text(Path(c.screenshot_path))
        if text:
            c.headline = text
            session.flush()
            n += 1
    return n
