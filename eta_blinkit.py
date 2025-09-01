from playwright.sync_api import sync_playwright, TimeoutError
import re

def normalize_eta(raw: str) -> str:
    """Extract minutes and return clean 'X min' format."""
    if not raw:
        return "N/A"
    raw = raw.strip().lower()
    m = re.search(r'(\d+)\s*min', raw)
    if m: return f"{m.group(1)} min"
    m = re.search(r'(\d+)', raw)
    if m: return f"{m.group(1)} min"
    return "N/A"

def _extract_eta(page, candidates: list[str], retries=3, delay=800) -> str:
    for _ in range(retries):
        for sel in candidates:
            try:
                el = page.locator(sel).first
                if el.count():
                    txt = (el.inner_text() or "").strip()
                    if txt:
                        return normalize_eta(txt)
            except Exception:
                continue
        page.wait_for_timeout(delay)
    return "N/A"

def get_blinkit_eta(latitude=18.5026501, longitude=73.8073136, headed=False) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            geolocation={"latitude": latitude, "longitude": longitude},
            permissions=["geolocation"],
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        page = context.new_page()
        eta = "N/A"
        try:
            page.goto("https://blinkit.com/", timeout=40000)
            try:
                page.locator("button.location-box").click(timeout=4000)
            except Exception:
                pass
            # wait for any element containing "min"
            try:
                page.wait_for_selector(":text('min')", timeout=8000)
            except Exception:
                pass
            raw = ""
            for sel in [
                "[data-testid='delivery-time']",
                "div.LocationBar__Title-sc-x8ezho-8",
                ":text('min')",
            ]:
                el = page.locator(sel).first
                if el.count():
                    raw = el.inner_text().strip()
                    break
            if not raw:
                raw = page.title()
            eta = normalize_eta(raw)
        finally:
            browser.close()
        return eta

if __name__ == "__main__":
    print("Blinkit ETA:", get_blinkit_eta())
