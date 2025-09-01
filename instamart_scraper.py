from playwright.sync_api import sync_playwright, TimeoutError

UA_MOBILE = (
    "Mozilla/5.0 (Linux; Android 10; Pixel 5 Build/QQ3A.200805.001; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

def run_instamart_mobile_scraper(search_query="bread", latitude=18.52, longitude=73.85, headed=True):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        context = browser.new_context(
            user_agent=UA_MOBILE,
            viewport={"width": 390, "height": 844},
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True,
            geolocation={"latitude": latitude, "longitude": longitude},
            permissions=["geolocation"],
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        context.add_init_script(
            'Object.defineProperty(navigator, "webdriver", { get: () => undefined });'
        )

        page = context.new_page()
        url = f"https://www.swiggy.com/instamart/search?custom_back=true&query={search_query.replace(' ', '%20')}"
        print(f"➡️ Opening Instamart (mobile) for: {search_query}")

        # --- Retry logic for load ---
        loaded = False
        for attempt in range(1, 4):  # up to 3 attempts
            try:
                print(f"🔄 Attempt {attempt}...")
                page.goto(url, timeout=45000)
                page.wait_for_timeout(2000)  # let it render

                # Detect "Something went wrong" screen
                if page.locator("div.ChSGx").first.is_visible():
                    print("⚠️ Error screen detected, retrying...")
                    continue

                # Wait until products load
                page.wait_for_selector("div.novMV", timeout=20000)
                loaded = True
                print("✅ Products loaded")
                break
            except TimeoutError:
                print("❌ No products loaded on this attempt")
                continue

        if not loaded:
            print("❌ Failed after retries")
            browser.close()
            return []

        # Scroll a few times to load more
        for _ in range(4):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)

        # Each product card = parent containing a name
        cards = page.query_selector_all("div:has(div.novMV)")
        print(f"🧩 Found {len(cards)} product cards")

        results = []
        for card in cards[:30]:  # limit for testing
            try:
                name_el = card.query_selector("div.novMV")
                qty_el = card.query_selector("div.entQHA")
                price_el = card.query_selector('div[data-testid="item-offer-price"]')
                img_el = card.query_selector("img.sc-dcJsrY")

                name = name_el.inner_text().strip() if name_el else ""
                qty = qty_el.inner_text().strip() if qty_el else "N/A"
                price = price_el.inner_text().strip() if price_el else "N/A"
                img = img_el.get_attribute("src") if img_el else ""

                results.append({
                    "platform": "instamart",
                    "name": name,
                    "quantity": qty,
                    "price": f"₹{price}" if price.isdigit() else price,
                    "image_url": img,
                    "product_url": url,
                    "delivery_time": "N/A",
                    "in_stock": True,
                })
            except Exception as e:
                print("⚠️ Card parse error:", e)
                continue

        browser.close()
        return results


if __name__ == "__main__":
    out = run_instamart_mobile_scraper("milk", headed=True)
    from pprint import pprint
    pprint(out[:10])
    print("Total:", len(out))
