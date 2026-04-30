from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from liveintent_shared.db import session_scope
from liveintent_shared.models import Advertiser, Creative, Impression
from ..auth import require_admin

router = APIRouter(prefix="/advertisers", tags=["advertisers"], dependencies=[Depends(require_admin)])

@router.get("")
def list_advertisers(days: int = Query(7, ge=1, le=90), vertical: str | None = None, limit: int = Query(50, le=500)):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    with session_scope() as s:
        stmt = (
            select(Advertiser.domain, Advertiser.vertical, func.count(Impression.id).label("c"))
            .join(Creative, Creative.advertiser_id == Advertiser.id)
            .join(Impression, Impression.creative_id == Creative.id)
            .where(Impression.seen_at >= since)
            .group_by(Advertiser.id, Advertiser.domain, Advertiser.vertical)
            .order_by(func.count(Impression.id).desc())
            .limit(limit)
        )
        if vertical:
            stmt = stmt.where(Advertiser.vertical == vertical)
        rows = s.execute(stmt).all()
        return [{"domain": d, "vertical": v, "impressions": int(c)} for d, v, c in rows]

@router.get("/{domain}")
def advertiser_detail(domain: str):
    with session_scope() as s:
        a = s.scalar(select(Advertiser).where(Advertiser.domain == domain))
        if not a:
            raise HTTPException(404, "not found")
        creatives = s.scalars(select(Creative).where(Creative.advertiser_id == a.id).order_by(Creative.last_seen_at.desc())).all()
        return {
            "domain": a.domain,
            "vertical": a.vertical,
            "vertical_source": a.vertical_source,
            "first_seen_at": a.first_seen_at.isoformat(),
            "last_seen_at": a.last_seen_at.isoformat(),
            "creatives": [
                {"id": c.id, "headline": c.headline, "screenshot_path": c.screenshot_path,
                 "image_url": c.image_url, "click_tracker_url": c.click_tracker_url,
                 "final_landing_url": c.final_landing_url, "last_seen_at": c.last_seen_at.isoformat()}
                for c in creatives
            ],
        }
