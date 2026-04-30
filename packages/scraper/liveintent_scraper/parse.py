"""LiveIntent / Zeta ad slot detector.

Real-world publisher emails wrap LiveIntent ads in their own click-tracker
(e.g. CNET → `links.email.cnet.com/...`, Morning Brew → `link.morningbrew.com/...`),
so matching the `<a href>` against `liveintent.com` / `zeta.com` does NOT work
for production emails. Only fixture/test emails have direct URLs.

The reliable detector is the **mandatory "Powered by ZETA" / "Powered by
LiveIntent"** branding text that LiveIntent inserts adjacent to every ad slot.
We locate that text, then walk back to the nearest enclosing `<a>` tag (or
the closest preceding `<a>` that wraps an `<img>`) — that's the ad slot.

We also keep the URL-based detector as a fallback for synthetic test emails
and any future direct-tracker case.
"""
import re
from bs4 import BeautifulSoup, Tag
from .selectors import AdSlot, LIVEINTENT_SELECTORS

# Matches the brand footer LiveIntent / Zeta places below each ad.
# Variants observed in the wild: "Powered by ZETA", "Powered by LiveIntent",
# "Ad by LiveIntent". Logos/icons (e.g. ◎ ⊕) often appear between "by" and the
# brand name, so we tolerate any non-letter chars in that gap.
ZETA_BRAND_RE = re.compile(
    r"(?:powered|ad)\s*by[\s\W]{0,15}(?:zeta|liveintent)",
    re.IGNORECASE,
)

# LiveIntent's server-side ad embed uses `sli.<publisher>.com/imp` impression
# pixels (e.g. sli.cnet.com/imp?s=...). The `lihide` CSS class is the
# fallback wrapper LiveIntent injects. Either is a strong slot signal even
# when the brand footer was stripped (e.g. forwarded emails).
LI_PIXEL_RE = re.compile(r'sli\.[a-z0-9-]+\.com/imp\?', re.IGNORECASE)
LIHIDE_CLASS_RE = re.compile(r'\b[a-zA-Z0-9_-]*lihide\b', re.IGNORECASE)


def _enclosing_ad_anchor(node: Tag) -> Tag | None:
    """Given a node containing the brand text, walk up/back to find the <a>
    that wraps the ad image."""
    cur: Tag | None = node
    while cur is not None:
        # If we're inside an <a>, return it.
        a = cur.find_parent("a")
        if a is not None and a.find("img") is not None:
            return a
        # Otherwise, look at preceding siblings of `cur`'s ancestors for
        # an <a><img></a> structure (brand text usually sits AFTER the ad).
        for sibling in cur.find_all_previous("a", limit=20):
            if sibling.find("img") is not None:
                return sibling
        cur = cur.parent
    return None


def _make_slot(a: Tag, *, slot_index: int, selector_used: str) -> AdSlot | None:
    href = a.get("href")
    if not href:
        return None
    img = a.find("img")
    img_src = img.get("src") if img else None
    return AdSlot(
        slot_index=slot_index,
        click_tracker_url=str(href),
        image_src=str(img_src) if img_src else None,
        selector_used=selector_used,
    )


def find_ad_slots(html: str) -> list[AdSlot]:
    soup = BeautifulSoup(html, "html.parser")
    slots: list[AdSlot] = []
    seen_anchors: set[int] = set()

    # 1. Brand-text-based detector (production-grade).
    for text_node in soup.find_all(string=ZETA_BRAND_RE):
        parent = text_node.parent if isinstance(text_node, str) else text_node
        if parent is None:
            continue
        a = _enclosing_ad_anchor(parent)
        if a is None:
            continue
        if id(a) in seen_anchors:
            continue
        seen_anchors.add(id(a))
        slot = _make_slot(a, slot_index=len(slots), selector_used="brand:zeta-text")
        if slot:
            slots.append(slot)

    # 1b. LiveIntent server-side embed pixel (sli.<pub>.com/imp). Each pixel
    # marks a slot — find the nearest enclosing <a><img> (the ad creative
    # may be sibling/parent). Useful even when brand text was stripped.
    for img in soup.find_all("img", src=LI_PIXEL_RE):
        a = _enclosing_ad_anchor(img)
        if a is None:
            # Some emails have the pixel as a tracking-only element with no
            # enclosing anchor (e.g. forwarded emails). Record an "unattributed"
            # slot so digest still shows publisher activity.
            slots.append(AdSlot(
                slot_index=len(slots),
                click_tracker_url=str(img.get("src", "")),
                image_src=str(img.get("src", "")),
                selector_used="pixel:sli-imp-no-anchor",
            ))
            continue
        if id(a) in seen_anchors:
            continue
        seen_anchors.add(id(a))
        slot = _make_slot(a, slot_index=len(slots), selector_used="pixel:sli-imp")
        if slot:
            slots.append(slot)

    # 1c. Elements with the lihide CSS class are LiveIntent's hide-wrappers.
    for el in soup.find_all(class_=LIHIDE_CLASS_RE):
        a = _enclosing_ad_anchor(el)
        if a is None:
            continue
        if id(a) in seen_anchors:
            continue
        seen_anchors.add(id(a))
        slot = _make_slot(a, slot_index=len(slots), selector_used="class:lihide")
        if slot:
            slots.append(slot)

    # 2. Legacy URL-based detector (test fixtures, edge cases).
    for selector in LIVEINTENT_SELECTORS:
        for a in soup.select(selector):
            if id(a) in seen_anchors:
                continue
            seen_anchors.add(id(a))
            slot = _make_slot(a, slot_index=len(slots), selector_used=selector)
            if slot:
                slots.append(slot)

    return slots
