"""
Blinkit platform scraper implementation.
"""

from typing import List, Dict, Any
from bs4 import BeautifulSoup

# Handle both individual testing and module imports
try:
    from .base import BaseScraper
except ImportError:
    # For individual testing
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from base import BaseScraper


class BlinkitScraper(BaseScraper):
    """Scraper implementation for Blinkit platform."""
    
    def get_platform_name(self) -> str:
        return "blinkit"
    
    def build_search_url(self, query: str) -> str:
        return f"https://blinkit.com/s/?q={query.replace(' ', '%20')}"
    
    def parse_products(self, page) -> List[Dict[str, Any]]:
        """Parse Blinkit products from the page."""
        # Wait for results grid
        self.try_until_success(lambda: page.wait_for_selector("div.categories__body", timeout=15000))
        
        # Remove popup modal if present
        self._remove_modal(page)
        
        # Scroll to load more results
        for _ in range(3):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            self._remove_modal(page)  # re-remove modal if it reappears
        
        # Grab HTML and parse with BeautifulSoup
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        card_divs = soup.find_all("div", {"role": "button", "id": True})
        
        results = []
        for card in card_divs:
            try:
                name_el = card.select_one("div.tw-text-300")
                price_el = card.select_one("div.tw-text-200.tw-font-semibold")
                qty_el = card.select_one("div.tw-text-200.tw-font-medium")
                img_el = card.select_one("img")
                
                name = name_el.get_text(strip=True) if name_el else ""
                price = price_el.get_text(strip=True) if price_el else "N/A"
                quantity = qty_el.get_text(strip=True) if qty_el else "N/A"
                image_url = img_el["src"] if img_el else ""
                product_id = card.get("id", "")
                product_url = f"https://blinkit.com/prn/x/prid/{product_id}" if product_id else ""
                
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
                print(f"⚠️ Error parsing card: {e}")
                continue
        
        return results
    
    def _remove_modal(self, page):
        """Remove popup modal if present."""
        page.evaluate("""
            () => {
                document.querySelectorAll('.LocationDropDown__LocationModalContainer-sc-bx29pc-0')
                  .forEach(e => e.remove());
            }
        """)


# Factory function to maintain backward compatibility
def run_scraper(search_query: str, headless: bool = True) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility."""
    scraper = BlinkitScraper(headless=headless)
    return scraper.scrape(search_query)


# Legacy functions for backward compatibility
def product_key(item: Dict[str, Any]) -> str:
    scraper = BlinkitScraper()
    return scraper.product_key(item)


def is_complete(item: Dict[str, Any]) -> bool:
    scraper = BlinkitScraper()
    return scraper.is_complete(item)


if __name__ == "__main__":
    # Manual test
    scraper = BlinkitScraper(headless=False)  # Set to True for production
    results = scraper.scrape("bread")
    
    from pprint import pprint
    pprint(results[:10])
    print("Total:", len(results))