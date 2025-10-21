# zepto_scraper.py
from playwright.sync_api import sync_playwright, TimeoutError
import re, time

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

def clean_price(price_str: str) -> str:
    match = re.search(r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', price_str or "")
    return f"₹{match.group(1)}" if match else "N/A"

def run_zepto_scraper(search_query: str):
    """Scrape Zepto using direct global search URL (no location flow)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # set False for debugging
            args=["--no-sandbox","--disable-dev-shm-usage","--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1440, "height": 900},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        context.add_init_script('Object.defineProperty(navigator, "webdriver", { get: () => undefined });')

        page = context.new_page()
        url = f"https://www.zeptonow.com/search?query={search_query.replace(' ', '%20')}"
        print(f"➡️ Opening Zepto global search for: {search_query}")
        page.goto(url, timeout=40000)

        try:
            page.wait_for_selector('a[href*="/pn/"]', timeout=20000)
        except TimeoutError:
            print("❌ Zepto: No product grid found")
            browser.close()
            return []

        # Scroll to load more results
        for _ in range(3):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(800)

        product_cards = page.query_selector_all('a[href*="/pn/"]')
        results = []

        for product in product_cards:
            try:
                name_el = product.query_selector('div[data-slot-id="ProductName"] span')
                qty_el  = product.query_selector('div[data-slot-id="PackSize"]')
                img_el  = product.query_selector('img')
                price_el = product.query_selector('p._price_ljyvk_11')

                name = (name_el.inner_text().strip() if name_el else "")
                quantity = (qty_el.inner_text().strip() if qty_el else "N/A")
                image_url = img_el.get_attribute("src") if img_el else ""
                price_text = price_el.inner_text().strip() if price_el else product.inner_text()
                price = clean_price(price_text)

                relative_url = product.get_attribute("href")
                product_url = f"https://www.zeptonow.com{relative_url}" if relative_url else ""

                results.append({
                    "platform": "zepto",
                    "name": name,
                    "price": price,
                    "quantity": quantity,
                    "image_url": image_url,
                    "product_url": product_url,
                    "in_stock": True,
                })
            except Exception as e:
                print(f"⚠️ Error parsing product: {e}")
                continue

        print(f"✅ Scraped {len(results)} items from Zepto")
        browser.close()
        return results

# required for app.py import
def product_key(item):
    return item.get("product_url")

def is_complete(item):
    return all([item.get("name"), item.get("price"), item.get("product_url")])

# --- Manual test ---
if __name__ == "__main__":
    out = run_zepto_scraper("amul milk")
    from pprint import pprint
    pprint(out[:10])
    print("Total:", len(out))