from playwright.sync_api import sync_playwright
import re

def normalize_eta(raw: str) -> str:
    """Clean raw ETA text like 'Delivery in 12 min' -> '12 min'."""
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

def get_blinkit_eta(address: str, headed: bool = False) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
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
            page.goto("https://blinkit.com/", timeout=40000)

            # Step 1: type into location search box
            search_box = page.locator('input[name="select-locality"]').first
            search_box.fill(address)
            page.wait_for_timeout(800)  # let suggestions appear

            # Step 2: click first suggestion
            suggestion = page.locator(
                "#app > div > div > div.containers__HeaderContainer-sc-1t9i1pe-0.jNcsdt "
                "> header > div.LocationDropDown__LocationModalContainer-sc-bx29pc-0.hxA-Dsy "
                "> div.location__shake-container-v1.animated > div > div > div.location-footer "
                "> div > div > div:nth-child(1)"
            )
            suggestion.click(timeout=5000)

            # Step 3: small wait for page to refresh ETA
            page.wait_for_timeout(2000)

            # Step 4: poll for ETA until available (max ~5s)
            raw = ""
            for _ in range(5):
                for sel in [
                    "[data-testid='delivery-time']",
                    "div.LocationBar__Title-sc-x8ezho-8",
                    ":text('min')",
                ]:
                    el = page.locator(sel).first
                    if el.count():
                        txt = (el.inner_text() or "").strip()
                        if txt:
                            raw = txt
                            break
                if raw:
                    break
                page.wait_for_timeout(1000)

            eta = normalize_eta(raw)

        finally:
            browser.close()

        return eta


if __name__ == "__main__":
    print("Blinkit ETA:", get_blinkit_eta("Azad Nagar, Kothrud"))