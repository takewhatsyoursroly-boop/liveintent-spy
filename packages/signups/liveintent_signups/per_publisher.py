"""Per-publisher Playwright signup flows.

The generic runner failed on these because each publisher hides their email
form behind a different interaction pattern (modal trigger, scroll-to-reveal,
multi-step). Each function here knows ONE publisher's flow.

Each function takes (page, persona) and returns (status, detail).
"""
from playwright.async_api import Page, TimeoutError as PWTimeout

from .personas import Persona


async def _safe_click(page: Page, selector: str, timeout: int = 3000) -> bool:
    try:
        loc = page.locator(selector).first
        if await loc.count() == 0:
            return False
        if not await loc.is_visible():
            return False
        await loc.click(timeout=timeout)
        return True
    except Exception:
        return False


async def _safe_fill(page: Page, selector: str, value: str, timeout: int = 2000) -> bool:
    try:
        loc = page.locator(selector).first
        if await loc.count() == 0:
            return False
        if not await loc.is_visible():
            return False
        await loc.fill(value, timeout=timeout)
        return True
    except Exception:
        return False


async def _success_text(page: Page) -> str:
    try:
        body = (await page.text_content("body") or "").lower()
    except Exception:
        return ""
    return body


async def signup_nyt(page: Page, persona: Persona) -> tuple[str, str]:
    """NYT: many newsletter cards. We pick "The Morning" (high-volume)."""
    await page.goto("https://www.nytimes.com/newsletters/the-morning",
                    wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(3000)
    # Cookie/GDPR banner
    await _safe_click(page, 'button:has-text("Accept")')
    await _safe_click(page, 'button[aria-label*="Accept" i]')
    # Click any "Subscribe" / "Sign Up" button to expose form
    await _safe_click(page, 'button:has-text("Sign up"), button:has-text("Subscribe")')
    await page.wait_for_timeout(2000)
    if not await _safe_fill(page, 'input[type="email"]', persona.email):
        return "no_form", "no_email_after_button"
    await _safe_click(page, 'button[type="submit"], button:has-text("Sign up"), button:has-text("Subscribe")')
    await page.wait_for_timeout(3000)
    body = await _success_text(page)
    return ("submitted", "ok") if "thank" in body or "subscribed" in body or "check" in body else ("submitted?", "no_text")


async def signup_theskimm(page: Page, persona: Persona) -> tuple[str, str]:
    await page.goto("https://www.theskimm.com/", wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(3000)
    # Scroll to footer where subscribe form usually lives
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(2000)
    if not await _safe_fill(page, 'input[type="email"]', persona.email):
        return "no_form", "no_email_in_footer"
    await _safe_click(page, 'button[type="submit"], button:has-text("Subscribe"), button:has-text("Sign up")')
    await page.wait_for_timeout(3000)
    body = await _success_text(page)
    return ("submitted", "ok") if "thank" in body or "subscribed" in body else ("submitted?", "no_text")


async def signup_cnet(page: Page, persona: Persona) -> tuple[str, str]:
    """CNET: click into a specific newsletter (CNET Insider) then signup form appears."""
    await page.goto("https://www.cnet.com/newsletters/", wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(4000)
    # Try clicking any "Sign Up" button on the page
    clicked = await _safe_click(page, 'button:has-text("Sign Up")')
    if not clicked:
        clicked = await _safe_click(page, 'a:has-text("Sign Up")')
    await page.wait_for_timeout(2500)
    if not await _safe_fill(page, 'input[type="email"]', persona.email):
        return "no_form", f"clicked={clicked}_no_email"
    await _safe_click(page, 'button[type="submit"], button:has-text("Sign Up"), button:has-text("Subscribe")')
    await page.wait_for_timeout(3000)
    body = await _success_text(page)
    return ("submitted", "ok") if "thank" in body or "subscribed" in body or "check" in body else ("submitted?", "no_text")


async def signup_bradsdeals(page: Page, persona: Persona) -> tuple[str, str]:
    await page.goto("https://www.bradsdeals.com/deal-alerts", wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(3000)
    # Brad's email form sometimes sits inline; sometimes triggered by scroll
    await page.evaluate("window.scrollTo(0, 600)")
    await page.wait_for_timeout(1500)
    if not await _safe_fill(page, 'input[type="email"]', persona.email):
        # Try after scroll-to-bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        if not await _safe_fill(page, 'input[type="email"]', persona.email):
            return "no_form", "no_email"
    await _safe_fill(page, 'input[name*="zip" i], input[id*="zip" i]', persona.zip_code)
    await _safe_click(page, 'button[type="submit"], button:has-text("Sign Up"), button:has-text("Subscribe")')
    await page.wait_for_timeout(3000)
    body = await _success_text(page)
    return ("submitted", "ok") if "thank" in body or "subscribed" in body or "welcome" in body else ("submitted?", "no_text")


async def signup_slickdeals(page: Page, persona: Persona) -> tuple[str, str]:
    """Slickdeals Money — trigger newsletter signup CTA."""
    await page.goto("https://money.slickdeals.net/newsletters/", wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(3000)
    await _safe_click(page, 'button:has-text("Sign Up"), button:has-text("Subscribe")')
    await page.wait_for_timeout(2000)
    if not await _safe_fill(page, 'input[type="email"]', persona.email):
        return "no_form", "no_email"
    await _safe_click(page, 'button[type="submit"], button:has-text("Subscribe"), button:has-text("Sign Up")')
    await page.wait_for_timeout(3000)
    body = await _success_text(page)
    return ("submitted", "ok") if "thank" in body or "subscribed" in body else ("submitted?", "no_text")


async def signup_patch(page: Page, persona: Persona) -> tuple[str, str]:
    """Patch: requires ZIP/town input first."""
    await page.goto("https://patch.com/subscribe", wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(3000)
    # Fill town/zip search first if present
    await _safe_fill(page, 'input[placeholder*="town" i], input[placeholder*="zip" i], input[name*="town" i], input[name*="location" i]', persona.zip_code)
    # Hit enter or click search
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(3000)
    # Now fill email
    if not await _safe_fill(page, 'input[type="email"]', persona.email):
        return "no_form", "no_email_after_zip"
    await _safe_click(page, 'button[type="submit"], button:has-text("Subscribe"), button:has-text("Sign Up")')
    await page.wait_for_timeout(3000)
    body = await _success_text(page)
    return ("submitted", "ok") if "thank" in body or "subscribed" in body else ("submitted?", "no_text")


async def signup_horoscope(page: Page, persona: Persona) -> tuple[str, str]:
    """Horoscope.com — has a multi-field form with birth-date dropdowns."""
    await page.goto("https://www.horoscope.com/us/emails/email-subscription.aspx",
                    wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(3000)
    # Fill email
    if not await _safe_fill(page, 'input[type="email"], input[name*="email" i]', persona.email):
        return "no_form", "no_email"
    # Fill name
    await _safe_fill(page, 'input[name*="first" i]', persona.first_name)
    await _safe_fill(page, 'input[name*="last" i]', persona.last_name)
    # Birth-year dropdown
    try:
        loc = page.locator('select[name*="year" i]').first
        if await loc.count():
            await loc.select_option(value=str(persona.birth_year))
    except Exception:
        pass
    # Gender
    try:
        loc = page.locator('select[name*="gender" i], select[name*="sex" i]').first
        if await loc.count():
            await loc.select_option(value=persona.gender)
    except Exception:
        pass
    # Check any "agree to terms" boxes
    for cb in await page.locator('input[type="checkbox"]:visible').all():
        try:
            if not await cb.is_checked(): await cb.check(timeout=500)
        except Exception:
            pass
    await _safe_click(page, 'button[type="submit"], input[type="submit"], button:has-text("Subscribe"), button:has-text("Sign Up")')
    await page.wait_for_timeout(3000)
    body = await _success_text(page)
    return ("submitted", "ok") if "thank" in body or "subscribed" in body or "success" in body else ("submitted?", "no_text")


async def signup_nysun(page: Page, persona: Persona) -> tuple[str, str]:
    """NY Sun: try the dedicated newsletter page."""
    for url in ["https://www.nysun.com/newsletters/", "https://www.nysun.com/subscribe", "https://www.nysun.com/"]:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)
        except Exception:
            continue
        # Scroll to find inline signup form
        for y in [0, 600, 1200, 2400]:
            await page.evaluate(f"window.scrollTo(0, {y})")
            await page.wait_for_timeout(1000)
            if await _safe_fill(page, 'input[type="email"]', persona.email):
                break
        else:
            continue
        await _safe_click(page, 'button[type="submit"], button:has-text("Subscribe"), button:has-text("Sign Up")')
        await page.wait_for_timeout(3000)
        body = await _success_text(page)
        return ("submitted", "ok") if "thank" in body or "subscribed" in body else ("submitted?", "no_text")
    return "no_form", "no_email_any_url"


SIGNUP_HANDLERS = {
    "nytimes.com":     ("NYT (The Morning)",  signup_nyt),
    "theskimm.com":    ("theSkimm",           signup_theskimm),
    "cnet.com":        ("CNET",               signup_cnet),
    "bradsdeals.com":  ("Brad's Deals",       signup_bradsdeals),
    "slickdeals.net":  ("Slickdeals Money",   signup_slickdeals),
    "patch.com":       ("Patch",              signup_patch),
    "horoscope.com":   ("Horoscope.com",      signup_horoscope),
    "nysun.com":       ("NY Sun",             signup_nysun),
}
