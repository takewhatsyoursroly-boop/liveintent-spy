from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from liveintent_shared.db import session_scope
from liveintent_shared.models import Publisher, Advertiser, Creative, Impression
from ..auth import require_admin

router = APIRouter(prefix="/publishers", tags=["publishers"], dependencies=[Depends(require_admin)])

@router.get("")
def list_publishers():
    with session_scope() as s:
        rows = s.scalars(select(Publisher).order_by(Publisher.domain)).all()
        return [{"domain": p.domain, "name": p.name, "active": p.active,
                 "last_email_received_at": p.last_email_received_at.isoformat() if p.last_email_received_at else None}
                for p in rows]

@router.get("/{domain}")
def publisher_detail(domain: str, days: int = Query(7, ge=1, le=90)):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    with session_scope() as s:
        p = s.scalar(select(Publisher).where(Publisher.domain == domain))
        if not p:
            raise HTTPException(404, "not found")
        rows = s.execute(
            select(Advertiser.domain, func.count(Impression.id).label("c"))
            .join(Creative, Creative.advertiser_id == Advertiser.id)
            .join(Impression, Impression.creative_id == Creative.id)
            .where(Impression.publisher_id == p.id)
            .where(Impression.seen_at >= since)
            .group_by(Advertiser.id, Advertiser.domain)
            .order_by(func.count(Impression.id).desc())
            .limit(50)
        ).all()
        return {
            "domain": p.domain, "name": p.name, "active": p.active,
            "top_advertisers": [{"domain": d, "impressions": int(c)} for d, c in rows],
        }
