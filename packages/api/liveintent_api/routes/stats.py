from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from liveintent_shared.db import session_scope
from liveintent_shared.models import Advertiser, Creative
from ..auth import require_admin

router = APIRouter(prefix="/stats", tags=["stats"], dependencies=[Depends(require_admin)])

@router.get("/cache")
def cache_stats(top: int = 10):
    """Image-cache hit rate and the advertisers most often missing a screenshot.

    `cached`: creatives whose image was downloaded by the enrichment worker.
    `still_empty`: creatives with image_url set but no cached file yet
        (fetch failed, tracking pixel filtered, or fetch hasn't run).
    `no_image_url`: creatives where the email had no <img src> at all
        (pure click-tracker slot — Fix #1B can't help these)."""
    with session_scope() as s:
        cached = s.scalar(select(func.count()).select_from(Creative).where(Creative.screenshot_path.like("%cached%"))) or 0
        still_empty = s.scalar(
            select(func.count()).select_from(Creative)
            .where(Creative.screenshot_path == "")
            .where(Creative.image_url.is_not(None))
        ) or 0
        no_image_url = s.scalar(
            select(func.count()).select_from(Creative).where(Creative.image_url.is_(None))
        ) or 0
        total = s.scalar(select(func.count()).select_from(Creative)) or 0

        rows = s.execute(
            select(Advertiser.domain, func.count(Creative.id))
            .join(Creative, Creative.advertiser_id == Advertiser.id)
            .where(Creative.screenshot_path == "")
            .where(Creative.image_url.is_not(None))
            .group_by(Advertiser.domain)
            .order_by(func.count(Creative.id).desc())
            .limit(top)
        ).all()
    return {
        "cached": cached,
        "still_empty": still_empty,
        "no_image_url": no_image_url,
        "total": total,
        "cached_ratio": (cached / total) if total else 0.0,
        "top_failing_advertisers": [{"domain": d, "missing": n} for d, n in rows],
    }
