# instamart_scraper.py
from playwright.sync_api import sync_playwright, TimeoutError
import time, re

def try_until_success(fn, retries=3, delay=0.8):
    for i in range(retries):
        try:
            return fn()
        except TimeoutError as e:
            print(f"⏳ Retry {i+1}/{retries}: {e}")
            time.sleep(delay)
    raise

RUPEE_RE = re.compile(r'₹\s*([0-9][0-9,]*(?:\.\d+)?)')

def run_instamart_scraper(search_query, address=None, latitude=18.502668, longitude=73.807327, headed=False):
    with sync_playwright() as p:
        UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")

        browser = p.chromium.launch(headless=False,
                                    args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1366, "height": 2000},
            geolocation={"latitude": latitude, "longitude": longitude},
            permissions=["geolocation"],
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        context.add_init_script('Object.defineProperty(navigator, "webdriver", { get: () => undefined });')

        page = context.new_page()

        # Navigate
        print("➡️ Navigating to Instamart")
        try_until_success(lambda: page.goto("https://www.swiggy.com/instamart", timeout=60000))

        # Use my location
        try:
            try_until_success(lambda: page.wait_for_selector('div[data-testid="set-gps-button"]', timeout=8000).click())
            print("📍 Used current location")
        except TimeoutError:
            print("⚠️ 'Use current location' not found; relying on geolocation injection")

        # Force geolocation
        page.evaluate(
            """({lat,lng})=>{
                const pos={coords:{latitude:lat,longitude:lng,accuracy:10},timestamp:Date.now()};
                try{navigator.geolocation.getCurrentPosition(cb=>cb(pos),()=>{})}catch(_){}
                try{navigator.geolocation.watchPosition(cb=>cb(pos),()=>{})}catch(_){}
            }""",
            {"lat": latitude, "lng": longitude},
        )

        # Search
        try:
            # 1) Click the fake/trigger search bar (best-effort; silently continues if absent)
            def click_trigger():
                # common patterns Instamart uses for the fake bar
                trigger_selectors = [
                    '._1AaZg',
                    '._1wmlH',
                ]
                for sel in trigger_selectors:
                    el = page.locator(sel).first
                    if el.count():
                        el.click(timeout=1000)
                        return True
                # as a last resort, click near the header area
                page.mouse.click(300, 120)  # harmless tap if nothing matched
                return True

            try_until_success(click_trigger, retries=2, delay=0.4)

            # 2) Now wait for the REAL input and submit
            try_until_success(
                lambda: page.wait_for_selector('input[placeholder*="Search"], input[type="search"]:not([readonly])',
                                            timeout=30000)
            )
            page.fill('input[placeholder*="Search"], input[type="search"]', search_query)
            page.keyboard.press("Enter")
        except TimeoutError:
            print("❌ Search bar interaction failed")
            browser.close()
            return []

        print("🔎 Searching for:", search_query)
        try_until_success(lambda: page.wait_for_selector('a[href*="/instamart/"], div[data-testid="product-card"]', timeout=45000))

        # Delivery time
        delivery_time = "N/A"
        try:
            dt = page.query_selector('._2AY8J')
            if dt:
                raw = (dt.inner_text() or "").strip().lower()
                m = re.search(r'(\d+)\s*min', raw)
                delivery_time = f"{m.group(1)} mins" if m else (raw or "N/A")
        except Exception:
            pass
                
        # Scroll to load more
        for _ in range(2):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(700)

        # Parse product cards
        cards = page.query_selector_all('a[href*="/instamart/"], div[data-testid="product-card"]')
        results = []

        for c in cards:
            try:
                name_el = c.query_selector('[data-testid="product-name"], h3, h4')
                price_el = c.query_selector('[data-testid="product-price"], p[class*="price"], [class*="price"] p')
                qty_el = c.query_selector('[data-testid="pack-size"], [class*="pack"], [class*="size"]')
                img_el = c.query_selector('img')

                name = (name_el.inner_text().strip() if name_el else "")
                price_text = price_el.inner_text() if price_el else c.inner_text()
                m = RUPEE_RE.search(price_text or "")
                price = f"₹{m.group(1)}" if m else "N/A"
                quantity = (qty_el.inner_text().strip() if qty_el else "N/A")
                image_url = img_el.get_attribute("src") if img_el else ""

                href = c.get_attribute("href") or ""
                product_url = "https://www.swiggy.com" + href if href.startswith("/") else href

                results.append({
                    "platform": "instamart",
                    "name": name,
                    "price": price,
                    "quantity": quantity,
                    "image_url": image_url,
                    "product_url": product_url,
                    "delivery_time": delivery_time,
                })
            except Exception as e:
                print(f"⚠️ Card parse error: {e}")
                continue

        print(f"✅ Scraped {len(results)} items")
        print(f"Delivery time: {delivery_time} min")
        browser.close()
        return results

# required for app.py import
def product_key(item):
    return item.get("product_url")

def is_complete(item):
    return all([item.get("name"), item.get("price"), item.get("product_url")])

# --- Manual test ---
if __name__ == "__main__":
    out = run_instamart_scraper("amul milk", "Kothrud, Pune 411038", latitude=18.502668, longitude=73.807327, headed=True)
    from pprint import pprint
    pprint(out)
