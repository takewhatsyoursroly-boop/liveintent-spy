from datetime import datetime, timedelta, timezone
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select, func
from liveintent_shared.db import session_scope
from liveintent_shared.models import Advertiser, Creative, Impression
from ..digest_compute import top_advertisers_by_vertical
from ..digest_format import format_digest_message
from ..telegram_client import TelegramClient

router = APIRouter(prefix="/telegram", tags=["telegram"])

class TgUpdate(BaseModel):
    update_id: int
    message: dict | None = None

def _handle_command(text: str) -> str:
    parts = text.strip().split()
    cmd = parts[0].lower() if parts else ""
    if cmd == "/topadvertisers":
        days = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        end = datetime.now(timezone.utc); start = end - timedelta(days=days)
        with session_scope() as s:
            data = top_advertisers_by_vertical(s, window_start=start, window_end=end, top_n=10)
        return format_digest_message(data, window_label=f"last {days}d")
    if cmd == "/advertiser" and len(parts) >= 2:
        domain = parts[1]
        end = datetime.now(timezone.utc); start = end - timedelta(days=7)
        with session_scope() as s:
            row = s.execute(
                select(func.count(Impression.id))
                .join(Creative, Creative.id == Impression.creative_id)
                .join(Advertiser, Advertiser.id == Creative.advertiser_id)
                .where(Advertiser.domain == domain)
                .where(Impression.seen_at >= start)
            ).scalar() or 0
            a = s.scalar(select(Advertiser).where(Advertiser.domain == domain))
            if not a:
                return f"`{domain}` not seen yet."
            return f"*{domain}*\nVertical: {a.vertical}\nImpressions (7d): {row}"
    if cmd == "/vertical" and len(parts) >= 2:
        vert = parts[1].lower()
        end = datetime.now(timezone.utc); start = end - timedelta(days=1)
        with session_scope() as s:
            data = top_advertisers_by_vertical(s, window_start=start, window_end=end, top_n=10)
        if vert not in data:
            return f"No `{vert}` advertisers in last 24h."
        return format_digest_message({vert: data[vert]}, window_label=f"last 24h — {vert}")
    return "Commands: /topadvertisers [days], /advertiser <domain>, /vertical <name>"

@router.post("/webhook")
def webhook(update: TgUpdate):
    if not update.message:
        return {"ok": True}
    chat_id = str(update.message.get("chat", {}).get("id", ""))
    text = update.message.get("text", "")
    if not chat_id or not text:
        return {"ok": True}
    reply = _handle_command(text)
    TelegramClient(chat_id=chat_id).send_message(reply)
    return {"ok": True}
