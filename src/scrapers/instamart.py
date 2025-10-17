"""
Instamart platform scraper implementation.
"""

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


class InstamartScraper(BaseScraper):
    """Scraper implementation for Instamart platform."""
    
    # Mobile User Agent for Instamart
    MOBILE_UA = (
        "Mozilla/5.0 (Linux; Android 10; Pixel 5 Build/QQ3A.200805.001; wv) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Mobile Safari/537.36"
    )
    
    MOBILE_VIEWPORT = {"width": 390, "height": 844}
    
    def __init__(self, latitude: float = 18.52, longitude: float = 73.85, **kwargs):
        super().__init__(**kwargs)
        self.latitude = latitude
        self.longitude = longitude
    
    def get_platform_name(self) -> str:
        return "instamart"
    
    def build_search_url(self, query: str) -> str:
        return f"https://www.swiggy.com/instamart/search?custom_back=true&query={query.replace(' ', '%20')}"
    
    def create_browser_context(self, playwright):
        """Create a mobile browser context for Instamart."""
        browser = playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        
        context = browser.new_context(
            user_agent=self.MOBILE_UA,
            viewport=self.MOBILE_VIEWPORT,
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True,
            geolocation={"latitude": self.latitude, "longitude": self.longitude},
            permissions=["geolocation"],
            locale=self.DEFAULT_LOCALE,
            timezone_id=self.DEFAULT_TIMEZONE,
        )
        
        context.add_init_script(
            'Object.defineProperty(navigator, "webdriver", { get: () => undefined });'
        )
        
        return browser, context
    
    def parse_products(self, page) -> List[Dict[str, Any]]:
        """Parse Instamart products from the page."""
        # Retry logic for loading
        loaded = False
        for attempt in range(1, 4):  # up to 3 attempts
            try:
                print(f"🔄 Attempt {attempt}...")
                page.wait_for_timeout(2000)  # let it render
                
                # Detect "Something went wrong" screen
                if page.locator("div.ChSGx").first.is_visible():
                    print("⚠️ Error screen detected, retrying...")
                    page.reload()
                    continue
                
                # Wait until products load
                page.wait_for_selector("div.novMV", timeout=20000)
                loaded = True
                print("✅ Products loaded")
                break
            except TimeoutError:
                print("❌ No products loaded on this attempt")
                if attempt < 3:
                    page.reload()
                continue
        
        if not loaded:
            print("❌ Failed after retries")
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
                    "platform": self.get_platform_name(),
                    "name": name,
                    "quantity": qty,
                    "price": f"₹{price}" if price.isdigit() else price,
                    "image_url": img,
                    "product_url": page.url,  # Use current page URL
                    "delivery_time": "N/A",
                    "in_stock": True,
                })
            except Exception as e:
                print("⚠️ Card parse error:", e)
                continue
        
        return results


def scrape_with_location(search_query: str, latitude: float = 18.52, longitude: float = 73.85) -> List[Dict[str, Any]]:
    """Scraper with custom location."""
    scraper = InstamartScraper(latitude=latitude, longitude=longitude)
    return scraper.scrape(search_query)


# Factory function to maintain backward compatibility
def run_instamart_mobile_scraper(search_query: str = "bread", latitude: float = 18.52, longitude: float = 73.85, headed: bool = True) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility."""
    scraper = InstamartScraper(latitude=latitude, longitude=longitude, headless=not headed)
    return scraper.scrape(search_query)


if __name__ == "__main__":
    scraper = InstamartScraper(headless=False)  # Set to True for production
    results = scraper.scrape("milk")
    
    from pprint import pprint
    pprint(results[:10])
    print("Total:", len(results))