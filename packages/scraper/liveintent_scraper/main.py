import asyncio
import sys
import time
from pathlib import Path
from imapclient import IMAPClient
import structlog
from liveintent_shared.config import get_settings
from liveintent_shared.db import session_scope
from liveintent_shared.logging import configure_logging
from .imap_poll import fetch_new_uids, fetch_message, parse_email_bytes, route_email_to_publisher, save_raw_html
from .render import browser_context, render_email_html
from .parse import find_ad_slots
from .screenshot import screenshot_slot
from .resolve import resolve_final_url, extract_advertiser_domain
from .persist import record_email, upsert_advertiser, upsert_creative, record_impression

log = structlog.get_logger(__name__)
LAST_UID_FILE = Path("./data/last_uid.txt")

def _load_last_uid() -> int:
    if LAST_UID_FILE.exists():
        return int(LAST_UID_FILE.read_text().strip() or "0")
    return 0

def _save_last_uid(uid: int) -> None:
    LAST_UID_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_UID_FILE.write_text(str(uid))

async def process_email(browser, raw: bytes, *, uid: int, data_dir: Path) -> None:
    parsed = parse_email_bytes(raw)
    with session_scope() as session:
        publisher = route_email_to_publisher(session, parsed.to_addr)
        if not publisher:
            log.info("scraper.unknown_recipient", to=parsed.to_addr, uid=uid)
            return
        html_path = save_raw_html(parsed.html_body, data_dir=data_dir / "emails_raw", imap_uid=uid)
        email_row = record_email(
            session, publisher_id=publisher.id, imap_uid=uid,
            subject=parsed.subject, from_addr=parsed.from_addr, raw_html_path=str(html_path),
        )
        session.flush()
        slots = find_ad_slots(parsed.html_body)
        if not slots:
            email_row.processed_at = _now()
            return
        try:
            page = await render_email_html(browser, parsed.html_body)
        except Exception as e:
            email_row.processing_error = f"render: {e}"
            email_row.processed_at = _now()
            return
        try:
            for slot in slots:
                try:
                    shot_path, digest = await screenshot_slot(
                        page, slot.slot_index, out_dir=data_dir / "screenshots"
                    )
                except Exception as e:
                    log.warning("scraper.screenshot_failed", uid=uid, slot=slot.slot_index, error=str(e))
                    continue
                final_url = resolve_final_url(slot.click_tracker_url)
                advertiser_domain = extract_advertiser_domain(final_url) if final_url else None
                if not advertiser_domain:
                    log.info("scraper.unresolved_advertiser", url=slot.click_tracker_url)
                    continue
                advertiser = upsert_advertiser(session, advertiser_domain)
                session.flush()
                creative = upsert_creative(
                    session, advertiser_id=advertiser.id, creative_hash=digest,
                    screenshot_path=str(shot_path), click_tracker_url=slot.click_tracker_url,
                )
                if final_url and not creative.final_landing_url:
                    creative.final_landing_url = final_url
                    creative.final_landing_url_resolved_at = _now()
                session.flush()
                record_impression(session, creative_id=creative.id, publisher_id=publisher.id, email_id=email_row.id)
            email_row.processed_at = _now()
        finally:
            await page.close()

def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)

async def run_once(data_dir: Path) -> None:
    settings = get_settings()
    last_uid = _load_last_uid()
    with IMAPClient(settings.imap_host, ssl=True) as client:
        client.login(settings.imap_user, settings.imap_pass)
        uids = fetch_new_uids(client, last_uid)
        if not uids:
            log.info("scraper.no_new_emails")
            return
        async with browser_context() as browser:
            for uid in uids:
                raw = fetch_message(client, uid)
                try:
                    await process_email(browser, raw, uid=uid, data_dir=data_dir)
                except Exception as e:
                    log.exception("scraper.process_failed", uid=uid, error=str(e))
                _save_last_uid(uid)

async def run_forever() -> None:
    settings = get_settings()
    data_dir = Path(settings.data_dir)
    while True:
        try:
            await run_once(data_dir)
        except Exception as e:
            log.exception("scraper.loop_iteration_failed", error=str(e))
        await asyncio.sleep(settings.scraper_poll_interval_seconds)

def main() -> None:
    configure_logging()
    asyncio.run(run_forever())

if __name__ == "__main__":
    main()
