import pytest
from pathlib import Path
from liveintent_scraper.render import browser_context, render_email_html
from liveintent_scraper.screenshot import screenshot_slot

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.mark.asyncio
async def test_screenshot_dedupes_by_hash(tmp_path):
    html = (FIXTURES / "sample_email_one_slot.html").read_text()
    async with browser_context() as browser:
        page = await render_email_html(browser, html)
        try:
            path1, hash1 = await screenshot_slot(page, 0, out_dir=tmp_path)
            path2, hash2 = await screenshot_slot(page, 0, out_dir=tmp_path)
            assert hash1 == hash2
            assert path1 == path2
            assert path1.exists()
        finally:
            await page.close()

@pytest.mark.asyncio
async def test_screenshot_out_of_range(tmp_path):
    html = (FIXTURES / "sample_email_one_slot.html").read_text()
    async with browser_context() as browser:
        page = await render_email_html(browser, html)
        try:
            with pytest.raises(ValueError):
                await screenshot_slot(page, 5, out_dir=tmp_path)
        finally:
            await page.close()
