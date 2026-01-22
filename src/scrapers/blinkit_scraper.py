"""
Blinkit Product Scraper - Direct API Implementation
Uses cloudscraper to bypass Cloudflare protection
~1-2s response time for 30 products (10-20x faster than Playwright)
"""

import cloudscraper
import time
import logging
import os
import uuid

logger = logging.getLogger(__name__)


def run_scraper(search_query: str, max_products: int = 30):
    """
    Scrape Blinkit products using direct API call with pagination
    
    Args:
        search_query: Product search query (e.g., "amul milk")
        max_products: Maximum number of products to fetch (default: 30)
    
    Returns:
        List of product dictionaries
    
    Performance: ~1-2 seconds for 30 products
    """
    
    try:
        start_time = time.time()
        all_products = []
        
        # Create cloudscraper session
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        # Blinkit search API endpoint
        url = "https://blinkit.com/v1/layout/search"
        
        # Headers - using env vars where applicable for configurability
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://blinkit.com',
            'Referer': f'https://blinkit.com/s/?q={search_query.replace(" ", "%20")}',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'app_client': 'consumer_web',
            'platform': 'desktop_web',
            'web_app_version': os.getenv('BLINKIT_WEB_APP_VERSION', '1008010016'),
            'app_version': os.getenv('BLINKIT_APP_VERSION', '1010101010'),
            'x-age-consent-granted': 'false',
            'access_token': 'null',
            'lat': os.getenv('BLINKIT_DEFAULT_LAT', '28.4652382'),
            'lon': os.getenv('BLINKIT_DEFAULT_LON', '77.0615957'),
            'device_id': str(uuid.uuid4())[:16],  # Generate unique device ID
            'session_uuid': str(uuid.uuid4()),     # Generate unique session
        }
        
        # First request - get initial products
        params = {
            'q': search_query,
            'search_type': 'type_to_search'
        }
        
        post_body = {
            "applied_filters": None,
            "monet_assets": [],
            "postback_meta": {},
            "previous_search_query": search_query,
            "processed_rails": {},
            "similar_entities": None,
            "sort": "",
            "vertical_cards_processed": 0
        }
        
        response = scraper.post(url, headers=headers, params=params, json=post_body, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            products = parse_search_response(data)
            all_products.extend(products)
            
            # If we need more products and there are more available, fetch next page
            if len(all_products) < max_products and len(products) > 0:
                # Second request - pagination
                params['offset'] = len(all_products)
                params['limit'] = 12
                params['page_index'] = 1
                
                response2 = scraper.post(url, headers=headers, params=params, json=post_body, timeout=10)
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    products2 = parse_search_response(data2)
                    all_products.extend(products2)
                    
                    # Third request if still need more
                    if len(all_products) < max_products and len(products2) > 0:
                        params['offset'] = len(all_products)
                        params['page_index'] = 2
                        
                        response3 = scraper.post(url, headers=headers, params=params, json=post_body, timeout=10)
                        
                        if response3.status_code == 200:
                            data3 = response3.json()
                            products3 = parse_search_response(data3)
                            all_products.extend(products3)
            
            # Limit to max_products
            all_products = all_products[:max_products]
            
            return all_products
        else:
            return []
            
    except Exception as e:
        logger.error(f"Blinkit scraper failed for '{search_query}': {e}")
        return []


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
        logger.warning(f"Failed to parse search response: {e}")
    
    return products


def is_product_snippet(snippet_data):
    """Check if a snippet contains product data"""
    return (isinstance(snippet_data, dict) and 
            'name' in snippet_data and 
            'image' in snippet_data and
            ('normal_price' in snippet_data or 'price' in snippet_data))


def parse_product_from_snippet(snippet_data):
    """Parse product data from API snippet"""
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
        
        # Build product URL
        product_url = f"https://blinkit.com/prn/x/prid/{product_id}" if product_id else ""
        
        # Extract inventory/stock status
        inventory = snippet_data.get('inventory', 0)
        in_stock = inventory > 0
        
        if name and name.strip():
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
        logger.debug(f"Failed to parse product snippet: {e}")
    
    return None


# Required for app.py imports
def product_key(item):
    return item.get("product_url")

def is_complete(item):
    return all([item.get("name"), item.get("price"), item.get("product_url")])


if __name__ == "__main__":
    print("Testing Blinkit scraper:")
    products = run_scraper("amul milk")
    print(f"Found {len(products)} products")
    if products:
        print("\nSample products:")
        for i, p in enumerate(products[:3], 1):
            print(f"{i}. {p['name']} - {p['price']}")
