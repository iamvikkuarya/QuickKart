# eta_zepto.py
from playwright.sync_api import sync_playwright
import re

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

def normalize_eta(raw: str) -> str:
    """Extract minutes and return clean 'X min' format."""
    if not raw:
        return "N/A"
    raw = raw.strip().lower()
    m = re.search(r'(\d+)\s*min', raw)
    if m:
        return f"{m.group(1)} min"
    m = re.search(r'(\d+)', raw)
    if m:
        return f"{m.group(1)} min"
    return "Store Unavailable / Closed"


def get_zepto_eta(address: str, headed: bool = False) -> str:
    """
    Fetch delivery ETA for Zepto.
    Requires a valid address string (validated upstream in app.py).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        page = context.new_page()
        eta = "N/A"

        context.route("**/*", lambda route: (
            route.abort() if route.request.resource_type in ["image", "font"] else route.continue_()
        ))

        try:
            page.goto("https://www.zeptonow.com/", timeout=40000)

            # Open location selector
            page.click('button[aria-label="Select Location"]', timeout=15000)
            page.fill('div[data-testid="address-search-input"] input', address)
            page.click('div[data-testid="address-search-item"]', timeout=20000)
            page.click('button[data-testid="location-confirm-btn"]', timeout=15000)

            # Wait for hydration + slight scroll
            page.wait_for_timeout(800)
            page.evaluate("window.scrollBy(0,300)")

            raw = ""
            for sel in [
                "[data-testid='delivery-time']",
                "span.font-extrabold",
                ":text('min')",
            ]:
                el = page.locator(sel).first
                if el.count():
                    raw = el.inner_text().strip()
                    break
            eta = normalize_eta(raw)

        finally:
            browser.close()
        return eta


if __name__ == "__main__":
    # Example: must pass explicit address
    print("Zepto ETA:", get_zepto_eta("Bavdhan, Pune"))
