from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup

app = Flask(__name__)

def run_scraper(search_query):
    results = []
    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir="./user_data",
            headless=True,
            viewport={"width": 411, "height": 731},
            user_agent="Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2)...",
            device_scale_factor=2.625,
            is_mobile=True,
            has_touch=True,
            locale="en-US",
            geolocation={"latitude": 18.5204, "longitude": 73.8567},
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
            html = card.inner_html()
            soup = BeautifulSoup(html, "html.parser")

            results.append({
                "name": soup.select_one("div.tw-text-300").get_text(strip=True) if soup.select_one("div.tw-text-300") else "N/A",
                "price": soup.select_one("div.tw-text-200.tw-font-semibold").get_text(strip=True) if soup.select_one("div.tw-text-200.tw-font-semibold") else "N/A",
                "quantity": soup.select_one("div.tw-text-200.tw-font-medium").get_text(strip=True) if soup.select_one("div.tw-text-200.tw-font-medium") else "N/A",
                "delivery_time": soup.select_one("div.tw-text-050").get_text(strip=True) if soup.select_one("div.tw-text-050") else "N/A",
                "image_url": soup.select_one("img")['src'] if soup.select_one("img") else "N/A",
                "product_url": url,
            })


        browser_context.close()
    return results

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query')
    if not query:
        return jsonify({"error": "Missing query"}), 400
    result = run_scraper(query)
    return jsonify(result)

@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)
