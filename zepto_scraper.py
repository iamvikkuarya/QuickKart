# zepto_scraper.py
from playwright.sync_api import sync_playwright
import re

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")

def clean_price(price_str):
    match = re.search(r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', price_str or "")
    return f"₹{match.group(1)}" if match else "N/A"

def clean_delivery_time(time_str):
    return (time_str or "").replace("\u200b", "").strip()

def run_zepto_scraper(query: str, address: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1366, "height": 2000},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        # reduce automation fingerprints slightly
        context.add_init_script(
            'Object.defineProperty(navigator, "webdriver", { get: () => undefined });'
        )

        page = context.new_page()
        page.goto("https://www.zeptonow.com/search", timeout=60000)

        # Location flow
        page.wait_for_selector('button[aria-label="Select Location"]', state="visible", timeout=15000)
        page.click('button[aria-label="Select Location"]')

        page.wait_for_selector('div[data-testid="address-search-input"] input', state="visible", timeout=15000)
        page.fill('div[data-testid="address-search-input"] input', address)

        # Wait for a populated suggestion item and select it
        page.wait_for_selector('div[data-testid="address-search-item"]', state="visible", timeout=20000)
        page.click('div[data-testid="address-search-item"]')

        page.wait_for_selector('button[data-testid="location-confirm-btn"]', state="visible", timeout=15000)
        page.click('button[data-testid="location-confirm-btn"]')

        # Search
        page.wait_for_selector('input[placeholder*="Search"]', state="visible", timeout=20000)
        page.fill('input[placeholder*="Search"]', query)
        page.keyboard.press("Enter")

        page.wait_for_selector('a[href*="/pn/"]', state="visible", timeout=30000)

        # Headless-safe scroll (5 passes)
        for _ in range(5):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(900)

        # Try to read a header-level delivery time; fall back to N/A
        delivery_el = page.query_selector('span.font-extrabold')
        delivery_time = clean_delivery_time(delivery_el.inner_text()) if delivery_el else "N/A"

        product_cards = page.query_selector_all('a[href*="/pn/"]')
        results = []
        parse_errors = 0

        for product in product_cards:
            try:
                # Ensure the card is hydrated/visible before reading text
                try:
                    product.scroll_into_view_if_needed()
                    page.wait_for_timeout(120)
                except Exception:
                    pass

                name_el = product.query_selector('div[data-slot-id="ProductName"] span')
                qty_el  = product.query_selector('div[data-slot-id="PackSize"]')
                img_el  = product.query_selector('img')

                # --- PRICE (using your provided selector with fallbacks) ---
                price_el = (
                    product.query_selector('p._price_ljyvk_11._price_lg_ljyvk_26')
                    or product.query_selector('_currency-symbol_ljyvk_49')
                )
                price_text = price_el.inner_text() if price_el else product.inner_text()
                price = clean_price(price_text)
                # -----------------------------------------------------------

                name = (name_el.inner_text().strip() if name_el else "").strip()
                quantity = (qty_el.inner_text().strip() if qty_el else "N/A")
                image_url = img_el.get_attribute('src') if img_el else ""
                relative_url = product.get_attribute('href')
                url = f"https://www.zeptonow.com{relative_url}" if relative_url else page.url

                results.append({
                    "platform": "zepto",
                    "name": name,
                    "price": price,
                    "quantity": quantity,
                    "image_url": image_url or "",
                    "product_url": url or "",
                    "delivery_time": delivery_time or "N/A",
                })
            except Exception:
                parse_errors += 1
                continue

        browser.close()
        return results
