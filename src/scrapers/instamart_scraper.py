"""
Swiggy Instamart Product Scraper
"""

from playwright.sync_api import sync_playwright
import threading
import logging

logger = logging.getLogger(__name__)

# Import geocoding only when not running as main (to avoid import issues in testing)
if __name__ != "__main__":
    from src.core.geocoding import geocode_address

# Thread-local storage for Playwright instances
_thread_local = threading.local()

def _get_browser():
    """Get or create Playwright browser instance (thread-local)"""
    if not hasattr(_thread_local, 'playwright') or _thread_local.browser is None or not _thread_local.browser.is_connected():
        _thread_local.playwright = sync_playwright().start()
        _thread_local.browser = _thread_local.playwright.chromium.launch(headless=True)
        _thread_local.context = _thread_local.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={'width': 1366, 'height': 768},
            locale="en-IN",
            timezone_id="Asia/Kolkata"
        )
        _thread_local.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)
    
    return _thread_local.context

def run_instamart_scraper(query, address):
    """
    Scrape products from Swiggy Instamart
    
    Args:
        query: Search query (e.g., "milk", "bread")
        address: Full address string
    
    Returns:
        list: List of product dictionaries
    """
    try:
        # Geocode address to lat/lng
        lat, lng = geocode_address(address)
        
        if lat is None or lng is None:
            return []
        
        # Get browser context
        context = _get_browser()
        page = context.new_page()
        
        try:
            # Initialize session
            page.goto(f"https://www.swiggy.com/instamart?lat={lat}&lng={lng}", timeout=30000)
            page.wait_for_timeout(2000)
            
            # Get store ID
            response = page.request.post(
                "https://www.swiggy.com/api/instamart/home/select-location/v2",
                data={
                    "data": {
                        "lat": lat,
                        "lng": lng,
                        "address": "",
                        "addressId": "",
                        "annotation": "",
                        "clientId": "INSTAMART-APP"
                    }
                },
                timeout=15000
            )
            
            if not response.ok:
                return []
            
            data = response.json()
            configs = data['data']['configs']['IM_PAGE_CONFIGS']['configInfo'][0]['card']
            store_id = configs['podDetailsList'][0]['podId']
            
            # Search for products
            url = f"https://www.swiggy.com/api/instamart/search/v2?offset=0&ageConsent=false&layoutId=4987&voiceSearchTrackingId=&storeId={store_id}&primaryStoreId={store_id}&secondaryStoreId="
            
            response = page.request.post(
                url,
                data={
                    "facets": [],
                    "sortAttribute": "",
                    "query": query,
                    "search_results_offset": "0",
                    "page_type": "INSTAMART_AUTO_SUGGEST_PAGE",
                    "is_pre_search_tag": False
                },
                timeout=15000
            )
            
            if not response.ok:
                return []
            
            data = response.json()
            
            # Extract products
            products = []
            
            def extract_products(obj):
                if isinstance(obj, dict):
                    if 'displayName' in obj and 'variations' in obj:
                        products.append(obj)
                    for value in obj.values():
                        if isinstance(value, (dict, list)):
                            extract_products(value)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_products(item)
            
            extract_products(data)
            
            # Format products for QuickKart
            formatted_products = []
            for product in products:
                # Get listing variant (or first variation)
                variation = None
                for v in product.get('variations', []):
                    if v.get('listingVariant', False):
                        variation = v
                        break
                
                if not variation and product.get('variations'):
                    variation = product['variations'][0]
                
                if variation:
                    price_info = variation.get('price', {})
                    
                    # Get image URL
                    image_ids = variation.get('imageIds', [])
                    image_url = None
                    if image_ids:
                        image_url = f"https://instamart-media-assets.swiggy.com/swiggy/image/upload/fl_lossy,f_auto,q_auto,h_600,w_600/{image_ids[0]}"
                    
                    # Get product URL
                    product_id = product.get('productId') or variation.get('spinId')
                    product_url = f"https://www.swiggy.com/instamart/item/{product_id}" if product_id else None
                    
                    # Format price
                    offer_price = price_info.get('offerPrice', {}).get('units', 0)
                    
                    formatted_products.append({
                        'name': product.get('displayName', ''),
                        'quantity': variation.get('quantityDescription', ''),
                        'platform': 'instamart',
                        'price': f"₹{offer_price}",
                        'product_url': product_url,
                        'image_url': image_url,
                        'in_stock': product.get('inStock', False)
                    })
            
            return formatted_products
        
        finally:
            page.close()
    
    except Exception as e:
        logger.error(f"Instamart scraper failed for '{query}': {e}")
        return []

def cleanup():
    """Cleanup Playwright resources"""
    if hasattr(_thread_local, 'browser') and _thread_local.browser:
        _thread_local.browser.close()
        _thread_local.browser = None
    
    if hasattr(_thread_local, 'playwright') and _thread_local.playwright:
        _thread_local.playwright.stop()
        _thread_local.playwright = None
    
    if hasattr(_thread_local, 'context'):
        _thread_local.context = None


# Test snippet
if __name__ == "__main__":
    import sys
    import os
    import time
    
    # Add project root to Python path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    import os
    
    # Add project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    # Import geocoding function for testing
    from src.core.geocoding import geocode_address
    
    # Get query and address from command line or use defaults
    query = sys.argv[1] if len(sys.argv) > 1 else "milk"
    address = sys.argv[2] if len(sys.argv) > 2 else "Viman Nagar, Pune"
    
    print(f"\n🛒 Testing Instamart Scraper")
    print(f"   Query: {query}")
    print(f"   Address: {address}")
    print("="*50)
    
    start_time = time.time()
    
    try:
        products = run_instamart_scraper(query, address)
        elapsed = time.time() - start_time
        
        if products:
            print(f"\n✅ SUCCESS!")
            print(f"   Found: {len(products)} products")
            print(f"   Time: {elapsed:.2f}s")
            print("\n📦 First 5 products:")
            
            for i, product in enumerate(products[:5], 1):
                print(f"\n{i}. {product['name']}")
                print(f"   Price: {product['price']}")
                print(f"   Quantity: {product['quantity']}")
                print(f"   In Stock: {product['in_stock']}")
                if product['product_url']:
                    print(f"   URL: {product['product_url']}")
        else:
            print(f"\n❌ No products found")
            print(f"   Time: {elapsed:.2f}s")
    
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ ERROR after {elapsed:.2f}s:")
        print(f"   {str(e)}")
    
    finally:
        cleanup()
        print(f"\n🧹 Cleanup completed")
