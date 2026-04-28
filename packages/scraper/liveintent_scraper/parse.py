from bs4 import BeautifulSoup
from .selectors import AdSlot, LIVEINTENT_SELECTORS

def find_ad_slots(html: str) -> list[AdSlot]:
    soup = BeautifulSoup(html, "html.parser")
    slots: list[AdSlot] = []
    seen_anchors: set[int] = set()

    for selector in LIVEINTENT_SELECTORS:
        for a in soup.select(selector):
            anchor_id = id(a)
            if anchor_id in seen_anchors:
                continue
            seen_anchors.add(anchor_id)
            href = a.get("href")
            if not href:
                continue
            img = a.find("img")
            img_src = img.get("src") if img else None
            slots.append(AdSlot(
                slot_index=len(slots),
                click_tracker_url=str(href),
                image_src=str(img_src) if img_src else None,
                selector_used=selector,
            ))
    return slots
