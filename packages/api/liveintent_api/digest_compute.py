from datetime import datetime
from collections import defaultdict
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from liveintent_shared.models import Advertiser, Creative, Impression
from liveintent_shared.enums import Vertical

def top_advertisers_by_vertical(
    session: Session, *, window_start: datetime, window_end: datetime, top_n: int = 10,
) -> dict[str, list[tuple[str, int]]]:
    """Returns {vertical -> [(domain, impression_count), ...]} sorted desc, capped at top_n.
    Excludes 'unclassified' advertisers."""
    stmt = (
        select(Advertiser.vertical, Advertiser.domain, func.count(Impression.id).label("c"))
        .join(Creative, Creative.advertiser_id == Advertiser.id)
        .join(Impression, Impression.creative_id == Creative.id)
        .where(Impression.seen_at >= window_start)
        .where(Impression.seen_at < window_end)
        .where(Advertiser.vertical != Vertical.UNCLASSIFIED.value)
        .group_by(Advertiser.id, Advertiser.vertical, Advertiser.domain)
    )
    rows = session.execute(stmt).all()
    by_vert: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for vert, domain, count in rows:
        by_vert[vert].append((domain, int(count)))
    return {v: sorted(items, key=lambda x: x[1], reverse=True)[:top_n] for v, items in by_vert.items()}
