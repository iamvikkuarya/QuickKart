from playwright.sync_api import sync_playwright, TimeoutError
import time
from bs4 import BeautifulSoup

# Retry utility
def try_until_success(fn, retries=3, delay=1):
    for i in range(retries):
        try:
            return fn()
        except TimeoutError as e:
            print(f"⏳ Retry {i+1}/{retries} after error: {e}")
            time.sleep(delay)
    raise TimeoutError("All retries failed")

def run_scraper(search_query, latitude=18.5204, longitude=73.8567):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            geolocation={"latitude": latitude, "longitude": longitude},
            permissions=["geolocation"]
        )
        page = context.new_page()

        print("➡️ Navigating to Blinkit")
        try_until_success(lambda: page.goto("https://blinkit.com/", timeout=30000))

        # Click Use My Location
        try:
            try_until_success(lambda: page.locator('button.location-box').click(timeout=3000), retries=2)
            print("📍 Location allowed")
        except TimeoutError:
            print("⚠️ Location button not found")

        # Search
        try:
            try_until_success(lambda: page.locator('div.SearchBar__Container-sc-16lps2d-3.ZIGuc').click(timeout=2000))
            input_box = try_until_success(lambda: page.wait_for_selector("input", timeout=1000))
            input_box.fill(search_query)
            input_box.press("Enter")
        except TimeoutError:
            print("❌ Search bar interaction failed")
            return []

        print("🔎 Searching for:", search_query)
        page.wait_for_timeout(2000)

        # Scroll slowly to load more cards
        last_height = 0
        for _ in range(2):
            page.mouse.wheel(0, 1000)
            time.sleep(1.0)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Wait for product card container
        try:
            container = try_until_success(lambda: page.wait_for_selector("div.categories__body", timeout=3000))
        except TimeoutError:
            print("❌ Product container not found")
            return []

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        card_divs = soup.find_all("div", {"role": "button", "id": True})

        results = []
        for card in card_divs:
            try:
                name = card.select_one("div.tw-text-300").get_text(strip=True)
                price = card.select_one("div.tw-text-200.tw-font-semibold").get_text(strip=True)
                quantity = card.select_one("div.tw-text-200.tw-font-medium").get_text(strip=True)
                image_url = card.select_one("img")["src"]
                delivery_time = card.select_one("div.tw-text-050").get_text(strip=True)
                product_id = card["id"]
                url = f"https://blinkit.com/prn/x/prid/{product_id}" if product_id else None

                results.append({
                    "name": name,
                    "price": price,
                    "quantity": quantity,
                    "image_url": image_url,
                    "delivery_time": delivery_time,
                    "product_url": url
                })
            except Exception as e:
                print(f"⚠️ Error parsing product card: {e}")
                continue

        print(f"✅ Scraped {len(results)} items")
        browser.close()
        return results

# required for app.py import
def product_key(item):
    return item.get("product_url")

def is_complete(item):
    return all([item.get("name"), item.get("price"), item.get("product_url")])
