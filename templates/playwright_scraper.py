"""
Playwright-based scraper MCP server template.

Wraps a web portal that has no API. Useful for sites requiring login and DOM scraping.
Pattern matches the Care Health Insurance MCP server approach.

Setup:
    uv add "fastmcp>=3.0" playwright
    uv run playwright install chromium

Run:
    PORTAL_USER=xxx PORTAL_PASS=yyy uv run server.py

Caveat: DOM scraping is fragile. When the portal redesigns, selectors break.
Treat this as a stopgap until a real API exists.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Annotated

from fastmcp import FastMCP
from playwright.async_api import async_playwright, Browser
from pydantic import Field

mcp = FastMCP("portal-scraper")

PORTAL_USER = os.environ.get("PORTAL_USER")
PORTAL_PASS = os.environ.get("PORTAL_PASS")
PORTAL_URL = os.environ.get("PORTAL_URL", "https://portal.example.com")

if not (PORTAL_USER and PORTAL_PASS):
    print("FATAL: PORTAL_USER and PORTAL_PASS env vars required", file=sys.stderr)
    sys.exit(1)


# Browser is expensive to start — keep one alive across calls
_browser: Browser | None = None


async def _get_browser() -> Browser:
    global _browser
    if _browser is None or not _browser.is_connected():
        pw = await async_playwright().start()
        _browser = await pw.chromium.launch(headless=True)
    return _browser


@asynccontextmanager
async def _logged_in_page():
    """Yield a page that's already authenticated to the portal."""
    browser = await _get_browser()
    context = await browser.new_context()
    page = await context.new_page()
    try:
        await page.goto(f"{PORTAL_URL}/login")
        await page.fill('input[name="username"]', PORTAL_USER)
        await page.fill('input[name="password"]', PORTAL_PASS)
        await page.click('button[type="submit"]')
        await page.wait_for_url(f"{PORTAL_URL}/dashboard", timeout=15000)
        yield page
    finally:
        await context.close()


@mcp.tool()
async def search_records(
    query: Annotated[str, Field(description="Search term entered into the portal's search box")],
    max_results: Annotated[int, Field(ge=1, le=50, default=10)] = 10,
) -> list[dict]:
    """Search the portal for records matching the query.

    Returns a list of records with their ID, title, and status. Scrapes the
    search results page directly — schema may break if the portal redesigns.
    """
    async with _logged_in_page() as page:
        await page.goto(f"{PORTAL_URL}/search")
        await page.fill('input[name="q"]', query)
        await page.press('input[name="q"]', "Enter")
        await page.wait_for_selector(".result-row", timeout=10000)

        rows = await page.query_selector_all(".result-row")
        results = []
        for row in rows[:max_results]:
            results.append({
                "id": await row.get_attribute("data-id") or "",
                "title": (await (await row.query_selector(".title")).inner_text()) if await row.query_selector(".title") else "",
                "status": (await (await row.query_selector(".status")).inner_text()) if await row.query_selector(".status") else "",
            })
        return results


@mcp.tool()
async def get_record_detail(
    record_id: Annotated[str, Field(description="Record ID from search_records")],
) -> dict:
    """Fetch the full detail page for a record. Returns all visible fields as a dict."""
    async with _logged_in_page() as page:
        await page.goto(f"{PORTAL_URL}/records/{record_id}")
        await page.wait_for_selector(".record-detail", timeout=10000)

        # Extract all .field-row elements as label: value pairs
        rows = await page.query_selector_all(".field-row")
        detail = {}
        for row in rows:
            label_el = await row.query_selector(".field-label")
            value_el = await row.query_selector(".field-value")
            if label_el and value_el:
                key = (await label_el.inner_text()).strip().rstrip(":")
                val = (await value_el.inner_text()).strip()
                detail[key] = val
        return detail


if __name__ == "__main__":
    mcp.run()
