from playwright.sync_api import sync_playwright, TimeoutError
import time
from bs4 import BeautifulSoup

# --- Tiny retry helper (for waiting on selectors reliably) ---
def try_until_success(fn, retries=3, delay=1.0):
    for i in range(retries):
        try:
            return fn()
        except TimeoutError:
            print(f"⏳ Retry {i+1}/{retries}")
            time.sleep(delay)
    raise TimeoutError("All retries failed")

def run_scraper(search_query: str):
    """Scrape Blinkit using the global search URL (no location required)."""
    with sync_playwright() as p:
        UA = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        browser = p.chromium.launch(
            headless=True,  # set False for debugging
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1440, "height": 900},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        context.add_init_script('Object.defineProperty(navigator, "webdriver", { get: () => undefined });')
        page = context.new_page()

        print(f"➡️ Opening Blinkit global search for: {search_query}")
        url = f"https://blinkit.com/s/?q={search_query.replace(' ', '%20')}"
        try_until_success(lambda: page.goto(url, timeout=40000))

        # Wait for results grid
        try_until_success(lambda: page.wait_for_selector("div.categories__body", timeout=15000))

        # Remove popup modal if present
        def remove_modal():
            page.evaluate("""
                () => {
                    document.querySelectorAll('.LocationDropDown__LocationModalContainer-sc-bx29pc-0')
                      .forEach(e => e.remove());
                }
            """)
        remove_modal()

        # Scroll to load more results
        for _ in range(3):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            remove_modal()  # re-remove modal if it reappears

        # Grab HTML and parse with BeautifulSoup
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        card_divs = soup.find_all("div", {"role": "button", "id": True})

        results = []
        for card in card_divs:
            try:
                name_el = card.select_one("div.tw-text-300")
                price_el = card.select_one("div.tw-text-200.tw-font-semibold")
                qty_el = card.select_one("div.tw-text-200.tw-font-medium")
                img_el = card.select_one("img")

                name = name_el.get_text(strip=True) if name_el else ""
                price = price_el.get_text(strip=True) if price_el else "N/A"
                quantity = qty_el.get_text(strip=True) if qty_el else "N/A"
                image_url = img_el["src"] if img_el else ""
                product_id = card.get("id", "")
                product_url = f"https://blinkit.com/prn/x/prid/{product_id}" if product_id else ""

                results.append({
                    "platform": "blinkit",
                    "name": name,
                    "price": price,
                    "quantity": quantity,
                    "image_url": image_url,
                    "product_url": product_url,
                    "in_stock": True,
                })
            except Exception as e:
                print(f"⚠️ Error parsing card: {e}")
                continue

        print(f"✅ Scraped {len(results)} items from Blinkit")
        browser.close()
        return results

# Required for app.py imports
def product_key(item):
    return item.get("product_url")

def is_complete(item):
    return all([item.get("name"), item.get("price"), item.get("product_url")])

# --- Manual Test ---
if __name__ == "__main__":
    out = run_scraper("amul milk")
    from pprint import pprint
    pprint(out[:10])
    print("Total:", len(out))