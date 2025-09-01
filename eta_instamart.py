from playwright.sync_api import sync_playwright, TimeoutError
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

def get_instamart_eta(latitude=18.5026501, longitude=73.8073136, headed=False) -> str:
    eta = "N/A"
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage","--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1366, "height": 900},
            geolocation={"latitude": latitude, "longitude": longitude},
            permissions=["geolocation"],
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        context.add_init_script('Object.defineProperty(navigator, "webdriver", { get: () => undefined });')
        page = context.new_page()

        try:
            page.goto("https://www.swiggy.com/instamart", timeout=60000)
            try:
                page.locator('div[data-testid="set-gps-button"]').click(timeout=8000)
            except TimeoutError:
                print("⚠️ 'Use current location' not found, relying on injected geolocation.")

            candidates = [
                "._2AY8J",
            ]
            eta = _extract_eta(page, candidates)
        except Exception as e:
            print("⚠️ Instamart ETA error:", e)
        finally:
            browser.close()
    return eta

if __name__ == "__main__":
    print("Instamart ETA:", get_instamart_eta())
