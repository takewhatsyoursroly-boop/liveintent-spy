import httpx
import tldextract
import structlog

log = structlog.get_logger(__name__)

def resolve_final_url(url: str, *, max_redirects: int = 10, timeout: float = 10.0) -> str | None:
    """Follow redirects from the click-tracker URL up to max_redirects.
    Returns the final URL on success, None on timeout/error/redirect-loop."""
    try:
        with httpx.Client(follow_redirects=False, timeout=timeout) as client:
            current = url
            for _ in range(max_redirects + 1):
                resp = client.get(current)
                if resp.status_code in (301, 302, 303, 307, 308):
                    loc = resp.headers.get("location")
                    if not loc:
                        return current
                    current = str(httpx.URL(current).join(loc))
                    continue
                return current
            log.warning("resolve.exceeded_redirect_budget", url=url)
            return None
    except (httpx.TimeoutException, httpx.HTTPError) as e:
        log.warning("resolve.http_error", url=url, error=str(e))
        return None

# LiveIntent's own infrastructure: tracking redirects, AdChoices/opt-out pages,
# pixel endpoints. These are NEVER advertisers — when a click resolves here it
# means we picked up a privacy link or pixel-only slot, not a real ad.
LIVEINTENT_INFRA_DOMAINS = frozenset({
    "liadm.com", "liveintent.com", "licasd.com", "lijit.com", "thrtle.com",
})

def extract_advertiser_domain(url: str) -> str | None:
    """Return eTLD+1 (e.g. 'newchapter.com') or None for invalid input or
    a LiveIntent infrastructure domain (which is never a real advertiser)."""
    try:
        ext = tldextract.extract(url)
        if not ext.domain or not ext.suffix:
            return None
        domain = f"{ext.domain}.{ext.suffix}"
        if domain in LIVEINTENT_INFRA_DOMAINS:
            return None
        return domain
    except Exception:
        return None
