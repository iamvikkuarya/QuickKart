from playwright.sync_api import sync_playwright
import re

def clean_price(price_str):
    match = re.search(r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', price_str)
    return f"₹{match.group(1)}" if match else "N/A"

def clean_delivery_time(time_str):
    return time_str.replace('\u200b', '').strip()

def run_zepto_scraper(query: str, address: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_context().new_page()

        page.goto("https://www.zeptonow.com/search", timeout=60000)
        page.click('button[aria-label="Select Location"]', timeout=15000)
        page.fill('div[data-testid="address-search-input"] input', address)
        page.wait_for_load_state("networkidle")
        page.click('div[data-testid="address-search-item"]')
        page.click('button[data-testid="location-confirm-btn"]')

        page.fill('input[placeholder="Search for over 5000 products"]', query)
        page.keyboard.press("Enter")
        page.wait_for_selector('a[href*="/pn/"]', timeout=20000)

        for _ in range(3):
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(1000)

        delivery_el = page.query_selector('span.font-extrabold')
        delivery_time = clean_delivery_time(delivery_el.inner_text()) if delivery_el else "N/A"

        product_cards = page.query_selector_all('a[href*="/pn/"]')
        results = []

        for product in product_cards:
            try:
                name = product.query_selector('div[data-slot-id="ProductName"] span').inner_text().strip()
                price = clean_price(product.query_selector('div[data-slot-id="Price"]').inner_text())
                quantity = product.query_selector('div[data-slot-id="PackSize"]').inner_text().strip()
                image = product.query_selector('img').get_attribute('src')
                relative_url = product.get_attribute('href')
                url = f"https://www.zeptonow.com{relative_url}" if relative_url else page.url

                results.append({
                    "name": name,
                    "price": price,
                    "quantity": quantity,
                    "image": image,
                    "url": url,
                    "delivery_time": delivery_time,
                    "source": "zepto"
                })
            except Exception as e:
                continue

        browser.close()
        return results

# Run the scraper with example query and address
if __name__ == "__main__":
    results = run_zepto_scraper("Amul", "Dadar, Mumbai")
    from pprint import pprint
    pprint(results)  # Print results nicely