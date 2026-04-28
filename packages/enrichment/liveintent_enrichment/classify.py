import os
import subprocess
import structlog
from anthropic import Anthropic
from liveintent_shared.config import get_settings

log = structlog.get_logger(__name__)

VALID_VERTICALS = ["supplements", "finance", "insurance", "sweeps", "auto", "solar", "health", "crypto", "other"]

PROMPT_TEMPLATE = """Classify this advertiser into exactly one of these verticals: {options}.

Respond with ONLY one word — the vertical name. No punctuation, no explanation.

Advertiser landing page text:
---
{text}
---"""

def _call_claude_api(prompt: str) -> str:
    """Direct Anthropic API call (fallback path)."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")
    client = Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=20,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip().lower()

def _call_claude_oauth(prompt: str) -> str:
    """Try `claude -p` OAuth path. Raises if claude CLI not found or fails."""
    proc = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude -p failed: {proc.stderr}")
    return proc.stdout.strip().lower()

def _call_claude(prompt: str) -> str:
    """Try OAuth first, fall back to API key."""
    try:
        return _call_claude_oauth(prompt)
    except Exception as oauth_err:
        log.info("classify.oauth_failed_falling_back", error=str(oauth_err))
        return _call_claude_api(prompt)

def classify_landing_page_text(text: str) -> str:
    """Returns one of VALID_VERTICALS, 'other', or 'unclassified' on hard error."""
    truncated = text[:4000]  # cap input
    prompt = PROMPT_TEMPLATE.format(options=", ".join(VALID_VERTICALS), text=truncated)
    try:
        raw = _call_claude(prompt)
    except Exception as e:
        log.warning("classify.failed", error=str(e))
        return "unclassified"
    word = raw.split()[0].strip(".,!?").lower() if raw else ""
    if word in VALID_VERTICALS:
        return word
    log.info("classify.invalid_response_to_other", got=raw)
    return "other"
