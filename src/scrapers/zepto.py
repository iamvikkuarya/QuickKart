"""
Zepto platform scraper implementation.
"""

import re
from typing import List, Dict, Any
from playwright.sync_api import TimeoutError

# Handle both individual testing and module imports
try:
    from .base import BaseScraper
except ImportError:
    # For individual testing
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from base import BaseScraper


class ZeptoScraper(BaseScraper):
    """Scraper implementation for Zepto platform."""
    
    def get_platform_name(self) -> str:
        return "zepto"
    
    def build_search_url(self, query: str) -> str:
        return f"https://www.zeptonow.com/search?query={query.replace(' ', '%20')}"
    
    def parse_products(self, page) -> List[Dict[str, Any]]:
        """Parse Zepto products from the page."""
        try:
            page.wait_for_selector('a[href*="/pn/"]', timeout=20000)
        except TimeoutError:
            print("❌ Zepto: No product grid found")
            return []
        
        # Scroll to load more results
        for _ in range(3):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(800)
        
        product_cards = page.query_selector_all('a[href*="/pn/"]')
        results = []
        
        for product in product_cards:
            try:
                name_el = product.query_selector('div[data-slot-id="ProductName"] span')
                qty_el = product.query_selector('div[data-slot-id="PackSize"]')
                img_el = product.query_selector('img')
                price_el = product.query_selector('p._price_ljyvk_11')
                
                name = name_el.inner_text().strip() if name_el else ""
                quantity = qty_el.inner_text().strip() if qty_el else "N/A"
                image_url = img_el.get_attribute("src") if img_el else ""
                price_text = price_el.inner_text().strip() if price_el else product.inner_text()
                price = self._clean_price(price_text)
                
                relative_url = product.get_attribute("href")
                product_url = f"https://www.zeptonow.com{relative_url}" if relative_url else ""
                
                results.append({
                    "platform": self.get_platform_name(),
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
        
        return results
    
    def _clean_price(self, price_str: str) -> str:
        """Clean and format price string."""
        match = re.search(r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', price_str or "")
        return f"₹{match.group(1)}" if match else "N/A"


# Factory function to maintain backward compatibility
def run_zepto_scraper(search_query: str, headless: bool = True) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility."""
    scraper = ZeptoScraper(headless=headless)
    return scraper.scrape(search_query)


# Legacy functions for backward compatibility
def product_key(item: Dict[str, Any]) -> str:
    scraper = ZeptoScraper()
    return scraper.product_key(item)


def is_complete(item: Dict[str, Any]) -> bool:
    scraper = ZeptoScraper()
    return scraper.is_complete(item)


def clean_price(price_str: str) -> str:
    """Legacy function for backward compatibility."""
    scraper = ZeptoScraper()
    return scraper._clean_price(price_str)


if __name__ == "__main__":
    # Manual test
    scraper = ZeptoScraper(headless=False)  # Set to True for production
    results = scraper.scrape("amul milk")
    
    from pprint import pprint
    pprint(results[:10])
    print("Total:", len(results))