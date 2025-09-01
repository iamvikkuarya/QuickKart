from playwright.sync_api import sync_playwright
import re

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

def normalize_eta(raw: str) -> str:
    if not raw: return "N/A"
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

def get_zepto_eta(address="Pune, Maharashtra", headed=False) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        page = context.new_page()
        eta = "N/A"
        try:
            page.goto("https://www.zeptonow.com/", timeout=40000)
            page.click('button[aria-label="Select Location"]', timeout=15000)
            page.fill('div[data-testid="address-search-input"] input', address)
            page.click('div[data-testid="address-search-item"]', timeout=20000)
            page.click('button[data-testid="location-confirm-btn"]', timeout=15000)

            # wait for hydration
            page.wait_for_timeout(500)
            # scroll a bit
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
    print("Zepto ETA:", get_zepto_eta("Azad Nagar, Kothrud, Pune"))
