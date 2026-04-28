from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Browser, Page

@asynccontextmanager
async def browser_context():
    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(headless=True)
        try:
            yield browser
        finally:
            await browser.close()

async def render_email_html(browser: Browser, html: str) -> Page:
    """Render email HTML in a fresh page, wait for network idle so LiveIntent
    pixel/ad-call resolves. Returns the Page (caller is responsible for closing)."""
    page = await browser.new_page()
    await page.set_content(html, wait_until="networkidle", timeout=30_000)
    return page
