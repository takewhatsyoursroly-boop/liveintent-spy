from dataclasses import dataclass

@dataclass(frozen=True)
class AdSlot:
    """One LiveIntent ad slot found in a rendered email."""
    slot_index: int           # 0-based position within the email
    click_tracker_url: str    # href of the wrapping <a>
    image_src: str | None     # src of the <img> if present
    selector_used: str        # which selector matched (for debug)

# CSS selectors for LiveIntent / Zeta ad slots, ordered by specificity.
# Stored as a list so we can hot-reload from DB later (R1 mitigation).
# LiveIntent was acquired by Zeta Global in Oct 2024; ads are now branded
# "Powered by ZETA" but the URL patterns still include legacy liveintent.com
# domains plus new zeta.com / zetaglobal.com tracker domains.
LIVEINTENT_SELECTORS: list[str] = [
    'a[href*="li/r/"]',
    'a[href*="track.liveintent.com"]',
    'a[href*="liveintent.com/r/"]',
    'a[href*="track.zeta.com"]',
    'a[href*="zetaglobal.com"]',
    'a[href*="zeta.com/r/"]',
]
