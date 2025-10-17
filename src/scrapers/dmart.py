"""
DMart platform scraper implementation.
"""

import requests
from typing import List, Dict, Any

# Handle both individual testing and module imports
try:
    from .base import BaseScraper
except ImportError:
    # For individual testing
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from base import BaseScraper


class DmartScraper(BaseScraper):
    """Scraper implementation for DMart platform."""
    
    # DMart API headers
    BASE_HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.dmart.in/",
        "Origin": "https://www.dmart.in",
    }
    
    def get_platform_name(self) -> str:
        return "dmart"
    
    def build_search_url(self, query: str) -> str:
        # DMart uses API endpoints, this won't be used directly
        return f"https://digital.dmart.in/api/v3/search/{query}"
    
    def scrape_with_store_id(self, search_query: str, store_id: str) -> List[Dict[str, Any]]:
        """
        Scrape products from DMart for a specific query and store.
        Store ID ensures results are location-specific.
        """
        url = f"https://digital.dmart.in/api/v3/search/{search_query}?page=1&size=100&channel=web&storeId={store_id}"
        
        try:
            resp = requests.get(url, headers=self.BASE_HEADERS, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            
            raw_products = data.get("products", [])
            print(f"🔎 totalRecords={data.get('totalRecords')}, products in JSON={len(raw_products)}")
            
            return self._parse_api_response(raw_products)
            
        except Exception as e:
            print(f"❌ Error scraping {self.get_platform_name()}: {e}")
            return []
    
    def parse_products(self, page) -> List[Dict[str, Any]]:
        """
        DMart uses API calls rather than page scraping.
        This method is not used but required by the abstract base class.
        """
        raise NotImplementedError("DMart scraper uses API calls, use scrape_with_store_id() instead")
    
    def _parse_api_response(self, raw_products: List[Dict]) -> List[Dict[str, Any]]:
        """Parse DMart API response into normalized product format."""
        products = []
        
        for product in raw_products:
            for sku in product.get("sKUs", []):
                try:
                    name = sku.get("name", "").strip()
                    price = sku.get("priceSALE")  # SALE price only
                    qty = sku.get("variantTextValue", "")
                    img_key = sku.get("productImageKey", "")
                    
                    # DMart image convention
                    image_url = f"https://cdn.dmart.in/images/products/{img_key}_5_P.jpg" if img_key else ""
                    
                    # Correct product URL format
                    seo_token = product.get("seo_token_ntk", "")
                    sku_id = sku.get("skuUniqueID")
                    product_url = f"https://www.dmart.in/product/{seo_token}?selectedProd={sku_id}" if seo_token and sku_id else ""
                    
                    products.append({
                        "platform": self.get_platform_name(),
                        "name": name,
                        "price": f"₹{price}" if price else "N/A",
                        "quantity": qty,
                        "image_url": image_url,
                        "product_url": product_url,
                        "delivery_time": "N/A",  # ETA handled separately
                        "in_stock": sku.get("buyable") == "true"
                    })
                except Exception as e:
                    print("⚠️ Error parsing SKU:", e)
                    continue
        
        print(f"✅ Parsed {len(products)} products from {self.get_platform_name()}")
        return products


# Factory function to maintain backward compatibility
def run_dmart_scraper(query: str, store_id: str) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility."""
    scraper = DmartScraper()
    return scraper.scrape_with_store_id(query, store_id)


if __name__ == "__main__":
    # Example: test with storeId
    test_store_id = "10680"  # Replace with real storeId
    scraper = DmartScraper()
    results = scraper.scrape_with_store_id("milk", test_store_id)
    print("✅ Sample product:", results[0] if results else "No results")