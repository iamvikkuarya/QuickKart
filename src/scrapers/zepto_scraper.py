# zepto_scraper.py - OPTIMIZED VERSION
# Uses API interception for 60% faster scraping (~4s vs ~10s)
from playwright.sync_api import sync_playwright, TimeoutError
import re
import logging

logger = logging.getLogger(__name__)

def clean_price(price_str: str) -> str:
    """Clean price string"""
    if not price_str:
        return "N/A"
    
    price_str = re.sub(r'\s+', ' ', str(price_str).strip())
    
    patterns = [
        r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*₹'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, price_str)
        if match:
            return f"₹{match.group(1)}"
    
    if '₹' in price_str:
        numbers = re.findall(r'₹\s*(\d+)', price_str)
        if numbers:
            return f"₹{numbers[0]}"
    
    return "N/A"

def run_zepto_scraper(search_query: str):
    """Optimized Zepto scraper using API interception"""
    
    products = []
    browser = None
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            
            # Stealth
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
            
            # Block images, fonts, media, CSS for speed
            context.route("**/*", lambda route: (
                route.abort() if route.request.resource_type in ['image', 'font', 'media', 'stylesheet']
                else route.continue_()
            ))
            
            page = context.new_page()
            
            # Intercept API response
            def handle_response(response):
                if '/api/v3/search' in response.url and response.status == 200:
                    try:
                        data = response.json()
                        layout = data.get('layout', [])
                        
                        for widget in layout:
                            widget_data = widget.get('data', {})
                            if not widget_data:
                                continue
                            
                            resolver = widget_data.get('resolver', {})
                            if not resolver:
                                continue
                            
                            resolver_data = resolver.get('data', {})
                            if not resolver_data:
                                continue
                            
                            items = resolver_data.get('items', [])
                            if not items:
                                continue
                            
                            # Check resolver type
                            resolver_type = resolver.get('type', '')
                            
                            if resolver_type == 'product_grid':
                                # Direct products in product_grid
                                for item in items:
                                    extract_product_direct(item, products)
                            else:
                                # Other types (ads, etc.) may have nested PRODUCT_ITEM
                                for item in items:
                                    if item.get('type') == 'PRODUCT_ITEM':
                                        extract_product(item, products)
                                    elif 'data' in item:
                                        nested_items = item.get('data', {}).get('items', [])
                                        if nested_items:
                                            for nested_item in nested_items:
                                                if nested_item.get('type') == 'PRODUCT_ITEM':
                                                    extract_product(nested_item, products)
                    except Exception as e:
                        logger.debug(f"Failed to parse API response: {e}")
            
            page.on('response', handle_response)
            
            # Navigate with optimal settings
            url = f"https://www.zeptonow.com/search?query={search_query.replace(' ', '%20')}"
            page.goto(url, timeout=15000, wait_until='domcontentloaded')
            
            # Wait for API response
            page.wait_for_timeout(3000)
            
    except Exception as e:
        logger.error(f"Zepto scraper failed for '{search_query}': {e}")
    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass
    
    return products

def extract_product_direct(item, products_list):
    """Extract product directly from product_grid items (new API structure)"""
    try:
        # New structure: productResponse wrapper
        product_response = item.get('productResponse', {})
        if not product_response:
            return
        
        product_info = product_response.get('product', {})
        variant_info = product_response.get('productVariant', {})
        
        name = product_info.get('name', '')
        # Price is now at top level of productResponse
        price = product_response.get('discountedSellingPrice') or product_response.get('sellingPrice', 0)
        
        if name and price:
            # Convert from paise to rupees
            price = price / 100
            
            image_url = ''
            images = variant_info.get('images', [])
            if images and len(images) > 0:
                img_path = images[0].get('path', '')
                if img_path:
                    image_url = f"https://cdn.zeptonow.com/{img_path}"
            
            quantity = variant_info.get('formattedPacksize', 'N/A')
            
            # Build proper URL: /pn/{slug}/pvid/{variant-id}
            variant_id = variant_info.get('id', '')
            # Create slug from product name - handle special characters
            import re
            slug = name.lower()
            slug = slug.replace('(', '').replace(')', '').replace('[', '').replace(']', '')
            slug = slug.replace(',', '').replace('.', '').replace('!', '').replace('?', '')
            slug = slug.replace('&', 'and').replace('+', 'plus')
            slug = slug.replace('/', '-').replace('\\', '-')
            slug = re.sub(r'[^\w\s-]', '', slug)  # Remove remaining special chars except spaces and hyphens
            slug = re.sub(r'\s+', '-', slug)  # Replace spaces with hyphens
            slug = re.sub(r'-+', '-', slug)  # Replace multiple hyphens with single
            slug = slug.strip('-')  # Remove leading/trailing hyphens
            product_url = f"https://www.zeptonow.com/pn/{slug}/pvid/{variant_id}" if variant_id else ""
            
            in_stock = not product_response.get('outOfStock', False)
            
            products_list.append({
                "platform": "zepto",
                "name": name,
                "price": f"₹{price:.0f}",
                "quantity": quantity,
                "image_url": image_url,
                "product_url": product_url,
                "in_stock": in_stock,
            })
    except Exception as e:
        logger.debug(f"Failed to extract product: {e}")

def extract_product(item, products_list):
    """Extract product from PRODUCT_ITEM (nested structure - fallback)"""
    try:
        item_data = item.get('data', {})
        product_info = item_data.get('product', {})
        variant_info = item_data.get('productVariant', {})
        
        name = product_info.get('name', '')
        price_obj = variant_info.get('price', {})
        price = price_obj.get('sp', 0) if price_obj else 0
        
        if name and price:
            image_url = ''
            images = variant_info.get('images', [])
            if images and len(images) > 0:
                img_path = images[0].get('path', '')
                if img_path:
                    image_url = f"https://cdn.zeptonow.com/{img_path}"
            
            quantity = variant_info.get('formattedPacksize', 'N/A')
            
            # Build proper URL
            variant_id = variant_info.get('id', '')
            slug = name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace(',', '')
            product_url = f"https://www.zeptonow.com/pn/{slug}/pvid/{variant_id}" if variant_id else ""
            
            in_stock = variant_info.get('isAvailable', True)
            
            products_list.append({
                "platform": "zepto",
                "name": name,
                "price": f"₹{price}",
                "quantity": quantity,
                "image_url": image_url,
                "product_url": product_url,
                "in_stock": in_stock,
            })
    except Exception as e:
        logger.debug(f"Failed to extract nested product: {e}")

# Required for app.py import
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
