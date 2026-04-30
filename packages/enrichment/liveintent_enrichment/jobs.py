from datetime import datetime, timezone, timedelta
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

_IMAGE_FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://mail.google.com/",
}

_EXT_BY_CONTENT_TYPE = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/avif": ".avif",
}

_MIN_IMAGE_BYTES = 1000      # smaller than this is almost certainly a 1x1 tracking pixel
_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5MB hard ceiling

def cache_pending_creative_images(session: Session, *, limit: int, data_dir: Path) -> int:
    """Download raw image_url from email HTML for creatives whose Playwright
    screenshot failed (screenshot_path == ''). Saves locally and updates the
    creative so the dashboard renders the cached file. Returns count cached.

    Re-attempts every iteration for unfilled rows — LiveIntent-style URLs can
    expire fast, so close-to-now-or-never. If volume grows we should add a
    `image_cache_attempted_at` column to back off."""
    pending = session.scalars(
        select(Creative)
        .where(Creative.screenshot_path == "")
        .where(Creative.image_url.is_not(None))
        .limit(limit)
    ).all()
    if not pending:
        return 0
    out_dir = data_dir / "screenshots" / "cached"
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    with httpx.Client(follow_redirects=True, timeout=10.0, headers=_IMAGE_FETCH_HEADERS) as client:
        for c in pending:
            url = c.image_url or ""
            if not url.startswith(("http://", "https://")):
                continue
            try:
                r = client.get(url)
            except Exception as e:
                log.warning("enrich.image_fetch_failed", creative_id=c.id, error=str(e))
                continue
            if r.status_code >= 400:
                log.info("enrich.image_fetch_status", creative_id=c.id, status=r.status_code)
                continue
            ct = r.headers.get("content-type", "").split(";")[0].strip().lower()
            ext = _EXT_BY_CONTENT_TYPE.get(ct)
            if not ext:
                log.info("enrich.image_bad_type", creative_id=c.id, ct=ct)
                continue
            body = r.content
            if len(body) < _MIN_IMAGE_BYTES:
                log.info("enrich.image_too_small", creative_id=c.id, bytes=len(body))
                continue
            if len(body) > _MAX_IMAGE_BYTES:
                log.info("enrich.image_too_large", creative_id=c.id, bytes=len(body))
                continue
            out_path = out_dir / f"{c.id}{ext}"
            out_path.write_bytes(body)
            c.screenshot_path = str(out_path)
            session.flush()
            n += 1
    return n

def retry_unresolved_creatives(session: Session, *, limit: int = 50, max_age_days: int = 7) -> int:
    """Retry click-tracker resolution for creatives where final_landing_url is null
    and the creative is younger than max_age_days. Returns count successfully resolved."""
    from liveintent_scraper.resolve import resolve_final_url, extract_advertiser_domain
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    pending = session.scalars(
        select(Creative)
        .where(Creative.final_landing_url.is_(None))
        .where(Creative.first_seen_at >= cutoff)
        .limit(limit)
    ).all()
    n = 0
    for c in pending:
        final = resolve_final_url(c.click_tracker_url)
        if not final:
            continue
        domain = extract_advertiser_domain(final)
        if not domain:
            continue
        c.final_landing_url = final
        c.final_landing_url_resolved_at = datetime.now(timezone.utc)
        # advertiser_id was set at first capture; we don't change it on retry
        session.flush()
        n += 1
    return n
