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
        if not c or not c.screenshot_path or not Path(c.screenshot_path).exists():
            raise HTTPException(404)
        # Starlette infers media_type from the file extension when omitted —
        # cached images may be png/jpg/gif/webp/avif, not just png.
        return FileResponse(c.screenshot_path)
