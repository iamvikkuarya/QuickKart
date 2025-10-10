"""
Base scraper class with common functionality for all platform scrapers.
"""

from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright, TimeoutError
import time
from typing import List, Dict, Any


class BaseScraper(ABC):
    """Abstract base class for all platform scrapers."""
    
    DEFAULT_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    DEFAULT_VIEWPORT = {"width": 1440, "height": 900}
    DEFAULT_LOCALE = "en-IN"
    DEFAULT_TIMEZONE = "Asia/Kolkata"
    
    def __init__(self, headless: bool = True, retries: int = 3, delay: float = 1.0):
        self.headless = headless
        self.retries = retries
        self.delay = delay
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name (e.g., 'blinkit', 'zepto')."""
        pass
    
    @abstractmethod
    def build_search_url(self, query: str) -> str:
        """Build the search URL for the given query."""
        pass
    
    @abstractmethod
    def parse_products(self, page) -> List[Dict[str, Any]]:
        """Parse products from the page and return normalized data."""
        pass
    
    def try_until_success(self, fn, retries: int = None, delay: float = None):
        """Retry helper for waiting on selectors reliably."""
        retries = retries or self.retries
        delay = delay or self.delay
        
        for i in range(retries):
            try:
                return fn()
            except TimeoutError:
                print(f"⏳ Retry {i+1}/{retries}")
                time.sleep(delay)
        raise TimeoutError("All retries failed")
    
    def create_browser_context(self, playwright):
        """Create a browser context with standard settings."""
        browser = playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ],
        )
        
        context = browser.new_context(
            user_agent=self.DEFAULT_UA,
            viewport=self.DEFAULT_VIEWPORT,
            locale=self.DEFAULT_LOCALE,
            timezone_id=self.DEFAULT_TIMEZONE,
        )
        
        # Hide webdriver property
        context.add_init_script(
            'Object.defineProperty(navigator, "webdriver", { get: () => undefined });'
        )
        
        return browser, context
    
    def scroll_page(self, page, scroll_count: int = 3, wait_time: int = 1000):
        """Scroll the page to load more content."""
        for _ in range(scroll_count):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(wait_time)
    
    def scrape(self, search_query: str) -> List[Dict[str, Any]]:
        """Main scraping method."""
        with sync_playwright() as p:
            browser, context = self.create_browser_context(p)
            page = context.new_page()
            
            try:
                url = self.build_search_url(search_query)
                print(f"➡️ Opening {self.get_platform_name()} search for: {search_query}")
                
                # Navigate to search page
                self.try_until_success(lambda: page.goto(url, timeout=40000))
                
                # Parse products using platform-specific logic
                results = self.parse_products(page)
                
                print(f"✅ Scraped {len(results)} items from {self.get_platform_name()}")
                return results
                
            except Exception as e:
                print(f"❌ Error scraping {self.get_platform_name()}: {e}")
                return []
            finally:
                browser.close()
    
    def product_key(self, item: Dict[str, Any]) -> str:
        """Generate a unique key for a product."""
        return item.get("product_url", "")
    
    def is_complete(self, item: Dict[str, Any]) -> bool:
        """Check if a product item has all required fields."""
        return all([item.get("name"), item.get("price"), item.get("product_url")])