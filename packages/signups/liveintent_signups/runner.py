"""Playwright-driven sign-up runner.

For each (publisher, persona) pair:
1. Open the subscribe URL in a fresh Chromium context (no shared cookies).
2. Try to fill an email + name form by querying common selectors.
3. Submit. Detect success/failure heuristically.
4. Wait for double-opt-in confirmation email on the catch-all box, then
   click the confirm link from a fresh browser context.

Failures are logged with reason; the runner moves on. The CLI summarizes
how many succeeded / pending-confirm / failed per persona.
"""
import asyncio
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from playwright.async_api import async_playwright, Page, BrowserContext, TimeoutError as PWTimeout
import structlog

from .personas import Persona, PERSONAS
from .publishers import Publisher, PUBLISHERS
from .inbox import fetch_confirm_emails

log = structlog.get_logger(__name__)

# A submit/subscribe form can use many different field names. Selectors are
# tried in order; first hit wins. All matching is case-insensitive and tolerant
# of common decoration (placeholder, aria-label, label-for).
EMAIL_SELECTORS = [
    'input[type="email"]',
    'input[name="email"]',
    'input[name="EMAIL"]',
    'input[name*="email" i]',
    'input[id*="email" i]',
    'input[placeholder*="email" i]',
    'input[aria-label*="email" i]',
]
FIRST_NAME_SELECTORS = [
    'input[name="firstName"]',
    'input[name="first_name"]',
    'input[name="FNAME"]',
    'input[name*="first" i]',
    'input[id*="firstname" i]',
    'input[placeholder*="first" i]',
]
LAST_NAME_SELECTORS = [
    'input[name="lastName"]',
    'input[name="last_name"]',
    'input[name="LNAME"]',
    'input[name*="last" i]',
    'input[id*="lastname" i]',
    'input[placeholder*="last" i]',
]
ZIP_SELECTORS = [
    'input[name="zip"]',
    'input[name="zipcode"]',
    'input[name="postalCode"]',
    'input[name*="zip" i]',
    'input[name*="postal" i]',
    'input[placeholder*="zip" i]',
]
SUBMIT_SELECTORS = [
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Subscribe")',
    'button:has-text("Sign Up")',
    'button:has-text("Sign up")',
    'button:has-text("Submit")',
    'button:has-text("Continue")',
    'button:has-text("Join")',
    'a:has-text("Subscribe"):visible',
]


@dataclass
class SignupResult:
    publisher_domain: str
    persona_alias: str
    status: str                 # "submitted" | "confirmed" | "captcha" | "no_form" | "error" | "skipped"
    detail: str = ""
    confirm_url_seen: str | None = None


async def _try_fill(page: Page, selectors: list[str], value: str) -> bool:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() == 0:
                continue
            if not await loc.is_visible():
                continue
            await loc.fill(value, timeout=2000)
            return True
        except Exception:
            continue
    return False


async def _try_click_submit(page: Page) -> bool:
    for sel in SUBMIT_SELECTORS:
        try:
            loc = page.locator(sel).first
            if await loc.count() == 0:
                continue
            if not await loc.is_visible():
                continue
            await loc.click(timeout=3000)
            return True
        except Exception:
            continue
    return False


async def _detect_captcha(page: Page) -> bool:
    """Quick heuristic — if reCAPTCHA / hCaptcha / Cloudflare-Turnstile iframe
    is visible, abort signup."""
    for sel in [
        'iframe[src*="recaptcha"]',
        'iframe[src*="hcaptcha"]',
        'iframe[src*="cf-turnstile"]',
        'iframe[title*="captcha" i]',
        '[class*="captcha"]',
    ]:
        try:
            if await page.locator(sel).count() > 0:
                return True
        except Exception:
            continue
    return False


async def _signup_one(
    context: BrowserContext, publisher: Publisher, persona: Persona,
) -> SignupResult:
    page = await context.new_page()
    try:
        try:
            await page.goto(publisher.subscribe_url, wait_until="domcontentloaded", timeout=30_000)
        except PWTimeout:
            return SignupResult(publisher.domain, persona.alias, "error", "page_load_timeout")

        # Quick captcha guard.
        if await _detect_captcha(page):
            return SignupResult(publisher.domain, persona.alias, "captcha", "captcha_detected")

        # Fill what we can find. Email is mandatory; name + zip are bonus.
        ok_email = await _try_fill(page, EMAIL_SELECTORS, persona.email)
        if not ok_email:
            return SignupResult(publisher.domain, persona.alias, "no_form", "no_email_field")
        await _try_fill(page, FIRST_NAME_SELECTORS, persona.first_name)
        await _try_fill(page, LAST_NAME_SELECTORS, persona.last_name)
        await _try_fill(page, ZIP_SELECTORS, persona.zip_code)

        # Some forms have a checkbox to accept terms — auto-check anything that
        # mentions "agree" / "consent" / "terms" if not already checked.
        try:
            for cb in await page.locator('input[type="checkbox"]').all():
                aria = (await cb.get_attribute("aria-label")) or ""
                if any(tok in aria.lower() for tok in ["agree", "consent", "terms", "subscribe"]):
                    if not await cb.is_checked():
                        await cb.check(timeout=1000)
        except Exception:
            pass

        if not await _try_click_submit(page):
            return SignupResult(publisher.domain, persona.alias, "error", "no_submit_button")

        # Allow time for client-side validation / redirect.
        try:
            await page.wait_for_load_state("networkidle", timeout=10_000)
        except PWTimeout:
            pass

        # Heuristic: did the page show "thanks", "confirm your inbox", or similar?
        try:
            body_text = (await page.text_content("body") or "").lower()
        except Exception:
            body_text = ""
        if any(tok in body_text for tok in [
            "thank you", "thanks for", "check your inbox", "confirm your subscription",
            "almost there", "confirmation email", "verify your email", "you're subscribed",
            "successfully subscribed",
        ]):
            return SignupResult(publisher.domain, persona.alias, "submitted", "success_text_visible")
        # Fall back: assume success if no error shown.
        if any(tok in body_text for tok in ["error", "invalid", "try again"]):
            return SignupResult(publisher.domain, persona.alias, "error", "error_text_visible")
        return SignupResult(publisher.domain, persona.alias, "submitted", "no_explicit_success")
    finally:
        try:
            await page.close()
        except Exception:
            pass


async def confirm_doi(
    context: BrowserContext, persona: Persona, *, imap_kwargs: dict, timeout_seconds: int = 120,
) -> list[str]:
    """Poll IMAP for confirmation emails to this persona, click each confirm
    link in a fresh browser tab. Returns list of confirm URLs visited."""
    visited: list[str] = []
    emails = fetch_confirm_emails(
        recipient=persona.email,
        timeout_seconds=timeout_seconds,
        **imap_kwargs,
    )
    log.info("doi.emails_found", persona=persona.alias, count=len(emails))
    for em in emails:
        if not em.confirm_url:
            log.info("doi.no_confirm_link", subject=em.subject, sender=em.from_addr)
            continue
        try:
            page = await context.new_page()
            try:
                await page.goto(em.confirm_url, wait_until="domcontentloaded", timeout=30_000)
                visited.append(em.confirm_url)
                log.info("doi.clicked", persona=persona.alias, sender=em.from_addr)
            finally:
                await page.close()
        except Exception as e:
            log.warning("doi.click_failed", url=em.confirm_url, error=str(e))
    return visited


async def run_signups(
    *, only_publishers: list[str] | None = None, only_personas: list[str] | None = None,
    confirm_doi_after: bool = True, imap_kwargs: dict | None = None,
    out_path: Path | None = None,
) -> list[SignupResult]:
    """Execute sign-ups for the cartesian product of (publishers, personas)
    after applying any filters. Returns the list of results."""
    pubs = [p for p in PUBLISHERS if not only_publishers or p.domain in only_publishers]
    personas = [p for p in PERSONAS if not only_personas or p.alias in only_personas]
    results: list[SignupResult] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            for persona in personas:
                # One context per persona — no cookies/state shared across personas.
                ctx = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/130.0.0.0 Safari/537.36"
                    ),
                    locale="en-US",
                )
                try:
                    for pub in pubs:
                        log.info("signup.start", publisher=pub.domain, persona=persona.alias)
                        result = await _signup_one(ctx, pub, persona)
                        results.append(result)
                        log.info("signup.done", publisher=pub.domain, persona=persona.alias,
                                 status=result.status, detail=result.detail)
                    if confirm_doi_after and imap_kwargs is not None:
                        visited = await confirm_doi(ctx, persona, imap_kwargs=imap_kwargs)
                        log.info("doi.summary", persona=persona.alias, clicked=len(visited))
                finally:
                    await ctx.close()
        finally:
            await browser.close()

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps([asdict(r) for r in results], indent=2))
    return results
