from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from liveintent_shared.db import session_scope
from liveintent_shared.models import Advertiser
from liveintent_shared.enums import Vertical, VerticalSource
from ..auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

class OverrideVerticalIn(BaseModel):
    vertical: str

@router.post("/advertisers/{domain}/vertical")
def override_vertical(domain: str, body: OverrideVerticalIn):
    if body.vertical not in [v.value for v in Vertical]:
        raise HTTPException(400, "invalid vertical")
    with session_scope() as s:
        a = s.scalar(select(Advertiser).where(Advertiser.domain == domain))
        if not a:
            raise HTTPException(404)
        a.vertical = body.vertical
        a.vertical_source = VerticalSource.MANUAL.value
        a.vertical_classified_at = datetime.now(timezone.utc)
    return {"ok": True, "domain": domain, "vertical": body.vertical}
