import gzip
import re
from dataclasses import dataclass
from pathlib import Path
from email import message_from_bytes
from email.message import Message
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from imapclient import IMAPClient
import structlog
from liveintent_shared.models import Publisher
from liveintent_shared.config import get_settings

log = structlog.get_logger(__name__)

@dataclass
class ParsedEmail:
    to_addr: str
    from_addr: str
    subject: str
    html_body: str

def _extract_html(msg: Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True) or b""
                return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        return ""
    if msg.get_content_type() == "text/html":
        payload = msg.get_payload(decode=True) or b""
        return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return ""

def parse_email_bytes(raw: bytes) -> ParsedEmail:
    msg = message_from_bytes(raw)
    return ParsedEmail(
        to_addr=(msg.get("To") or "").strip(),
        from_addr=(msg.get("From") or "").strip(),
        subject=(msg.get("Subject") or "").strip(),
        html_body=_extract_html(msg),
    )

_FROM_EMAIL_RE = re.compile(r"<\s*([^<>\s]+@[^<>\s]+)\s*>|([^<>\s]+@[^<>\s]+)")


def _extract_email_address(header_value: str) -> str | None:
    """Pull the bare email out of a 'Display Name <local@domain>' header."""
    if not header_value:
        return None
    m = _FROM_EMAIL_RE.search(header_value)
    if not m:
        return None
    return (m.group(1) or m.group(2) or "").strip().lower()


def route_email_to_publisher(session: Session, header_value: str) -> Publisher | None:
    """Match incoming email to a Publisher by FROM address.

    Accepts the raw From header (e.g. 'Morning Brew <crew@morningbrew.com>')
    and matches it against Publisher.from_address (case-insensitive)."""
    email = _extract_email_address(header_value)
    if not email:
        return None
    return session.scalar(
        select(Publisher).where(func.lower(Publisher.from_address) == email)
    )

def save_raw_html(html: str, *, data_dir: Path, imap_uid: int) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    out = data_dir / f"{imap_uid}.html.gz"
    out.write_bytes(gzip.compress(html.encode("utf-8")))
    return out

def fetch_new_uids(client: IMAPClient, since_uid: int) -> list[int]:
    """Returns sorted list of UIDs strictly greater than since_uid."""
    client.select_folder("INBOX", readonly=False)
    uids = client.search(["UID", f"{since_uid + 1}:*"])
    return sorted(u for u in uids if u > since_uid)

def fetch_message(client: IMAPClient, uid: int) -> bytes:
    data = client.fetch([uid], ["RFC822"])
    return data[uid][b"RFC822"]
