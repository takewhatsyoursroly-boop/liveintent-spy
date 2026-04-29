import hashlib
from pathlib import Path
from playwright.async_api import Page
from .selectors import LIVEINTENT_SELECTORS

async def screenshot_slot(page: Page, slot_index: int, *, out_dir: Path) -> tuple[Path, str]:
    """Screenshot the Nth LiveIntent slot in the page. Returns (path, sha256_hash).
    Raises ValueError if the slot can't be located."""
    locators = page.locator(", ".join(LIVEINTENT_SELECTORS))
    count = await locators.count()
    if slot_index >= count:
        raise ValueError(f"slot_index {slot_index} out of range (found {count})")
    out_dir.mkdir(parents=True, exist_ok=True)
    bytes_ = await locators.nth(slot_index).screenshot(type="png")
    digest = hashlib.sha256(bytes_).hexdigest()
    out_path = out_dir / f"{digest}.png"
    if not out_path.exists():
        out_path.write_bytes(bytes_)
    return out_path, digest
