from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy import select
from liveintent_shared.db import session_scope
from liveintent_shared.models import Creative
from ..auth import require_admin

router = APIRouter(prefix="/creatives", tags=["creatives"], dependencies=[Depends(require_admin)])

@router.get("/{creative_id}/screenshot")
def creative_screenshot(creative_id: int):
    with session_scope() as s:
        c = s.scalar(select(Creative).where(Creative.id == creative_id))
        if not c or not Path(c.screenshot_path).exists():
            raise HTTPException(404)
        return FileResponse(c.screenshot_path, media_type="image/png")
