from playwright.sync_api import sync_playwright, TimeoutError
import time

def run_scraper(search_query: str):
    """Blinkit scraper using API interception."""
    products = []
    
    with sync_playwright() as p:
        UA = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Simple browser setup 
        browser = p.chromium.launch(
            headless=True,  # set False for debugging
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(user_agent=UA)
        page = context.new_page()

        #Simple resource blocking
        context.route("**/*", lambda route: (
            route.abort() if route.request.resource_type in ["image", "font", "stylesheet"] 
            else route.continue_()
        ))

        #Intercept API responses
        def handle_response(response):
            nonlocal products
            url = response.url
            
            # Capture search API responses
            if '/v1/layout/search' in url and response.status == 200:
                try:
                    data = response.json()
                    new_products = parse_search_response(data)
                    products.extend(new_products)
                    print(f"✅ API: Found {len(new_products)} more products (total: {len(products)})")
                except Exception as e:
                    print(f"⚠️ Error parsing API response: {e}")
        
        page.on('response', handle_response)

        print(f"➡️ Opening Blinkit search for: {search_query}")
        url = f"https://blinkit.com/s/?q={search_query.replace(' ', '%20')}"
        
        try:
            print(f"⚡ Fast search for: {search_query}")
            start_time = time.time()
            
            # Navigate to search page
            page.goto(url, timeout=20000)
            print(f"   ✅ Page loaded in {time.time() - start_time:.2f}s")
            
            # Wait for initial API responses
            page.wait_for_timeout(3000)
            
            # Quick scroll to trigger pagination APIs
            scroll_start = time.time()
            for i in range(2):  # Reduced from 3 to 2 scrolls
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)
                
                # Early exit if we have enough products
                if len(products) >= 40:
                    print(f"   ⚡ Early exit: Got {len(products)} products")
                    break
            
            print(f"   ✅ Scrolling completed in {time.time() - scroll_start:.2f}s")
            
            # Remove duplicates based on product URL
            unique_products = []
            seen_urls = set()
            for product in products:
                url = product.get('product_url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_products.append(product)
            
            print(f"✅ Scraped {len(unique_products)} items from Blinkit (API method)")
            return unique_products
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            return []
        finally:
            browser.close()

def parse_search_response(data):
    """Parse the JSON response from Blinkit's search API"""
    products = []
    
    try:
        if not data.get('is_success'):
            return products
        
        response = data.get('response', {})
        snippets = response.get('snippets', [])
        
        for snippet in snippets:
            if isinstance(snippet, dict) and 'data' in snippet:
                snippet_data = snippet['data']
                
                # Check if this snippet contains product data
                if is_product_snippet(snippet_data):
                    product = parse_product_from_snippet(snippet_data)
                    if product:
                        products.append(product)
                        
    except Exception as e:
        print(f"⚠️ Error parsing search response: {e}")
    
    return products

def is_product_snippet(snippet_data):
    """🔍 Check if a snippet contains product data"""
    return (isinstance(snippet_data, dict) and 
            'name' in snippet_data and 
            'image' in snippet_data and
            ('normal_price' in snippet_data or 'price' in snippet_data))

def parse_product_from_snippet(snippet_data):
    """📦 Parse product data from API snippet to match original format"""
    try:
        # Extract name
        name_obj = snippet_data.get('name', {})
        name = name_obj.get('text', '') if isinstance(name_obj, dict) else str(name_obj)
        
        # Extract price
        price_obj = snippet_data.get('normal_price') or snippet_data.get('price', {})
        price = price_obj.get('text', 'N/A') if isinstance(price_obj, dict) else str(price_obj)
        
        # Extract variant/quantity
        variant_obj = snippet_data.get('variant', {})
        quantity = variant_obj.get('text', 'N/A') if isinstance(variant_obj, dict) else str(variant_obj)
        
        # Extract image
        image_obj = snippet_data.get('image', {})
        image_url = image_obj.get('url', '') if isinstance(image_obj, dict) else str(image_obj)
        
        # Extract product ID for URL
        identity = snippet_data.get('identity', {})
        product_id = identity.get('id', '') if isinstance(identity, dict) else ''
        
        # Build product URL (same format as original)
        product_url = f"https://blinkit.com/prn/x/prid/{product_id}" if product_id else ""
        
        # Extract inventory/stock status (additional data not in original)
        inventory = snippet_data.get('inventory', 0)
        in_stock = inventory > 0
        
        if name and name.strip():
            # Return same format as original scraper
            return {
                "platform": "blinkit",
                "name": name.strip(),
                "price": price,
                "quantity": quantity,
                "image_url": image_url,
                "product_url": product_url,
                "in_stock": in_stock,
            }
            
    except Exception as e:
        print(f"⚠️ Error parsing product snippet: {e}")
    
    return None

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