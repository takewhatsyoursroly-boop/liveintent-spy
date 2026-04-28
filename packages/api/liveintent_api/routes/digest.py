import json
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from liveintent_shared.db import session_scope
from liveintent_shared.models import DigestRun
from ..auth import require_admin
from ..digest_compute import top_advertisers_by_vertical
from ..digest_format import format_digest_message
from ..telegram_client import TelegramClient

router = APIRouter(prefix="/digest", tags=["digest"], dependencies=[Depends(require_admin)])

@router.post("/run")
def run_digest(window_hours: int = 24):
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=window_hours)
    with session_scope() as s:
        data = top_advertisers_by_vertical(s, window_start=start, window_end=end, top_n=10)
        msg = format_digest_message(data, window_label=f"last {window_hours}h")
        message_id: str | None = None
        try:
            message_id = TelegramClient().send_message(msg)
        except Exception as e:
            # Don't fail the digest if Telegram is down — record it anyway
            pass
        s.add(DigestRun(
            window_start=start, window_end=end,
            top_advertisers_json=json.dumps({k: v for k, v in data.items()}),
            telegram_message_id=message_id,
        ))
    return {"ok": True, "telegram_message_id": message_id, "verticals": list(data.keys())}

@router.get("/today")
def get_today():
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    with session_scope() as s:
        return top_advertisers_by_vertical(s, window_start=start, window_end=end, top_n=10)
