# blinkit_scraper.py

from playwright.sync_api import sync_playwright, TimeoutError

def product_key(product):
    return product.get("product_url", "").strip().lower()

def is_complete(product):
    return product.get("image_url") not in ["", "N/A", None] and product.get("price") not in ["", "N/A", None]

def run_scraper(search_query, latitude=None, longitude=None):
    # Fallback to Pune if no location provided
    latitude = latitude if latitude is not None else 18.5204
    longitude = longitude if longitude is not None else 73.8567

    results = []
    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir="./user_data",
            headless=False,
            viewport={"width": 411, "height": 731},
            user_agent="Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2)...",
            device_scale_factor=2.625,
            is_mobile=True,
            has_touch=True,
            locale="en-US",
            geolocation={"latitude": latitude, "longitude": longitude},
            permissions=["geolocation"],
        )

        page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
        page.goto("https://www.blinkit.com", wait_until="domcontentloaded")

        try:
            page.locator('div.DownloadAppModal__BackButtonIcon-sc-1wef47t-14').click(timeout=1000)
        except TimeoutError:
            pass

        try:
            page.locator('div.GetLocationModal__ButtonContainer-sc-jc7b49-5 > div:nth-child(1)').click(timeout=1000)
        except TimeoutError:
            pass

        try:
            page.locator('div.SearchBar__Container-sc-16lps2d-3.ZIGuc > a').click(timeout=5000)
            input_box = page.wait_for_selector("input", timeout=5000)
            input_box.fill(search_query)
            input_box.press("Enter")
        except TimeoutError:
            return []

        for _ in range(5):
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(1000)

        cards = page.query_selector_all('div[style*="grid-column: span 6"]')

        for card in cards:
            prod_id = card.get_attribute("id")
            if not prod_id:
                continue

            url = f"https://blinkit.com/prn/x/prid/{prod_id}"
            image_element = card.query_selector("img")
            image_url = image_element.get_attribute("src") if image_element else "N/A"

            results.append({
                "name": card.query_selector("div.tw-text-300").inner_text().strip() if card.query_selector("div.tw-text-300") else "N/A",
                "price": card.query_selector("div.tw-text-200.tw-font-semibold").inner_text().strip() if card.query_selector("div.tw-text-200.tw-font-semibold") else "N/A",
                "quantity": card.query_selector("div.tw-text-200.tw-font-medium").inner_text().strip() if card.query_selector("div.tw-text-200.tw-font-medium") else "N/A",
                "delivery_time": card.query_selector("div.tw-text-050").inner_text().strip() if card.query_selector("div.tw-text-050") else "N/A",
                "image_url": image_url,
                "product_url": url,
            })

        browser_context.close()
    return results
