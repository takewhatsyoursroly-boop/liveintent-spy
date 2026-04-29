"""IMAP utilities for monitoring the catch-all inbox during signup.

After we submit a signup form, the publisher typically sends a double-opt-in
confirmation email. This module polls IMAP for those emails, extracts the
confirm link, and the runner clicks it to finalize the subscription.
"""
import re
import time
import gzip
from dataclasses import dataclass
from email import message_from_bytes
from email.message import Message
from imapclient import IMAPClient
from bs4 import BeautifulSoup
import structlog

log = structlog.get_logger(__name__)


@dataclass
class ConfirmEmail:
    uid: int
    to_addr: str
    from_addr: str
    subject: str
    confirm_url: str | None  # Best-guess URL to click


# Heuristics for finding the confirmation link in a sign-up email body.
# Ordered most-specific first; first match wins.
CONFIRM_LINK_PATTERNS = [
    # Anchor text containing typical confirmation phrases.
    re.compile(r"confirm\s+(?:your\s+)?(?:subscription|email|signup)", re.IGNORECASE),
    re.compile(r"verify\s+(?:your\s+)?email", re.IGNORECASE),
    re.compile(r"activate\s+(?:your\s+)?(?:account|subscription)", re.IGNORECASE),
    re.compile(r"complete\s+(?:your\s+)?(?:signup|subscription|registration)", re.IGNORECASE),
    re.compile(r"^\s*click\s+here\s*$", re.IGNORECASE),
    re.compile(r"^\s*confirm\s*$", re.IGNORECASE),
    re.compile(r"^\s*subscribe\s*$", re.IGNORECASE),
]


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


def _extract_text(msg: Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True) or b""
                return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        return ""
    if msg.get_content_type() == "text/plain":
        payload = msg.get_payload(decode=True) or b""
        return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return ""


def find_confirm_url(html: str, plain_text: str = "") -> str | None:
    """Heuristically find the most likely 'confirm subscription' URL in an
    email body. Tries anchor text patterns first, then falls back to the
    first URL in plain text containing 'confirm'/'verify'/'activate'."""
    soup = BeautifulSoup(html, "html.parser")
    for pattern in CONFIRM_LINK_PATTERNS:
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            if pattern.search(text):
                return str(a["href"])
    # Fallback: any anchor whose href contains a likely token.
    for a in soup.find_all("a", href=True):
        href = str(a["href"]).lower()
        if any(tok in href for tok in ["confirm", "verify", "activate", "optin", "double-opt", "doi"]):
            return str(a["href"])
    # Plain-text fallback: scan URLs in plain part.
    for line in plain_text.splitlines():
        for word in line.split():
            w = word.strip(",.;()<>\"'")
            if w.startswith(("http://", "https://")) and any(
                tok in w.lower() for tok in ["confirm", "verify", "activate", "optin", "doi"]
            ):
                return w
    return None


def fetch_confirm_emails(
    *, host: str, user: str, password: str, port: int, ssl: bool, recipient: str,
    timeout_seconds: int = 120, poll_interval: int = 5,
) -> list[ConfirmEmail]:
    """Poll IMAP looking for new emails to `recipient` (e.g. r.alvarez@clearmindskin.com).
    Returns up to all confirm-style emails seen within `timeout_seconds`. Empty list
    if nothing arrived in time."""
    deadline = time.time() + timeout_seconds
    found: list[ConfirmEmail] = []
    seen_uids: set[int] = set()

    kwargs: dict = {"ssl": ssl}
    if port:
        kwargs["port"] = port

    while time.time() < deadline:
        try:
            with IMAPClient(host, **kwargs) as c:
                c.login(user, password)
                c.select_folder("INBOX", readonly=False)
                # Search for unread mail addressed to this recipient.
                uids = c.search(["TO", recipient])
                for uid in uids:
                    if uid in seen_uids:
                        continue
                    seen_uids.add(uid)
                    raw = c.fetch([uid], ["RFC822"])[uid][b"RFC822"]
                    msg = message_from_bytes(raw)
                    to_addr = (msg.get("To") or "").strip()
                    if recipient.lower() not in to_addr.lower():
                        continue
                    html = _extract_html(msg)
                    text = _extract_text(msg)
                    confirm = find_confirm_url(html, text)
                    found.append(ConfirmEmail(
                        uid=uid,
                        to_addr=to_addr,
                        from_addr=(msg.get("From") or "").strip(),
                        subject=(msg.get("Subject") or "").strip(),
                        confirm_url=confirm,
                    ))
        except Exception as e:
            log.warning("inbox.poll_failed", error=str(e))
        if found:
            return found
        time.sleep(poll_interval)
    return found
