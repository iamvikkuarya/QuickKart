# zepto_scraper.py
from playwright.sync_api import sync_playwright, TimeoutError
import re, time, random

# Enhanced user agents for better stealth
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

UA = random.choice(USER_AGENTS)  # Maintain compatibility with existing code

def clean_price(price_str: str) -> str:
    """Enhanced price cleaning with multiple patterns"""
    if not price_str:
        return "N/A"
    
    # Clean up whitespace and newlines
    price_str = re.sub(r'\s+', ' ', price_str.strip())
    
    # Multiple price patterns
    patterns = [
        r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # ₹29 or ₹ 29
        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*₹'   # 29₹
    ]
    
    for pattern in patterns:
        match = re.search(pattern, price_str)
        if match:
            return f"₹{match.group(1)}"
    
    # Handle split rupee symbol and number
    if '₹' in price_str:
        numbers = re.findall(r'₹\s*(\d+)', price_str)
        if numbers:
            return f"₹{numbers[0]}"
    
    return "N/A"

def run_zepto_scraper(search_query: str):
    """Scrape Zepto using direct global search URL (no location flow)."""
    with sync_playwright() as p:
        # Enhanced browser launch with optimizations
        browser = p.chromium.launch(
            headless=True,  # set False for debugging
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--disable-extensions"
            ],
        )
        
        # Enhanced context with better stealth
        context = browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1440, "height": 900},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            extra_http_headers={
                "Accept-Language": "en-IN,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br"
            }
        )
        
        # Enhanced resource blocking for speed (keep images for product display)
        context.route("**/*", lambda route: (
            route.abort() if route.request.resource_type in ["font", "media"] 
            else route.continue_()
        ))
        
        # Enhanced stealth
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
        """)

        page = context.new_page()
        url = f"https://www.zeptonow.com/search?query={search_query.replace(' ', '%20')}"
        print(f"➡️ Opening Zepto global search for: {search_query}")
        page.goto(url, timeout=30000)  # Reduced timeout

        try:
            # Enhanced product detection with multiple selectors
            product_selectors = ['a[href*="/pn/"]', '[data-testid*="product"]', '.product-card']
            products_found = False
            
            for selector in product_selectors:
                try:
                    page.wait_for_selector(selector, timeout=10000)  # Reduced timeout
                    products_found = True
                    break
                except TimeoutError:
                    continue
            
            if not products_found:
                print("❌ Zepto: No product grid found")
                browser.close()
                return []
        except Exception as e:
            print(f"❌ Zepto: Error waiting for products: {e}")
            browser.close()
            return []

        # Enhanced scrolling with reduced waits
        for _ in range(3):
            page.evaluate("window.scrollBy(0, window.innerHeight)")  # More efficient scrolling
            page.wait_for_timeout(500)  # Reduced wait time

        product_cards = page.query_selector_all('a[href*="/pn/"]')
        results = []

        for product in product_cards:
            try:
                # Enhanced name extraction
                name_el = product.query_selector('div[data-slot-id="ProductName"] span')
                name = (name_el.inner_text().strip() if name_el else "")
                
                # Enhanced price extraction with updated selectors
                price_text = ""
                price_container = product.query_selector('div[data-slot-id="Price"]')
                if price_container:
                    price_elements = price_container.query_selector_all('p')
                    if price_elements:
                        price_text = price_elements[0].inner_text().strip()
                
                # Fallback price extraction
                if not price_text:
                    price_el = product.query_selector('p._price_ljyvk_11')
                    price_text = price_el.inner_text().strip() if price_el else ""
                
                if not price_text:
                    # Try scanning all p elements for price
                    p_elements = product.query_selector_all('p')
                    for p_el in p_elements:
                        text = p_el.inner_text().strip()
                        if "₹" in text and len(text) < 20:
                            price_text = text
                            break
                
                if not price_text:
                    price_text = product.inner_text()
                
                price = clean_price(price_text)
                
                # Skip products without essential data
                if not name or price == "N/A":
                    continue

                # Enhanced quantity extraction
                qty_el = product.query_selector('div[data-slot-id="PackSize"]')
                quantity = (qty_el.inner_text().strip() if qty_el else "N/A")
                
                # Enhanced image extraction
                image_url = ""
                img_el = product.query_selector('img')
                if img_el:
                    for attr in ['src', 'data-src', 'data-lazy-src']:
                        url = img_el.get_attribute(attr)
                        if url and url.startswith('http'):
                            image_url = url
                            break

                # Enhanced product URL extraction
                relative_url = product.get_attribute("href")
                product_url = ""
                if relative_url:
                    if relative_url.startswith('http'):
                        product_url = relative_url
                    else:
                        product_url = f"https://www.zeptonow.com{relative_url}"

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