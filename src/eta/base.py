"""
Base ETA class with common functionality for all platform ETA fetchers.
"""

import re
from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright
from typing import Optional


class BaseETA(ABC):
    """Abstract base class for all platform ETA fetchers."""
    
    DEFAULT_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    DEFAULT_VIEWPORT = {"width": 1366, "height": 768}
    DEFAULT_LOCALE = "en-IN"
    DEFAULT_TIMEZONE = "Asia/Kolkata"
    
    def __init__(self, headless: bool = True, timeout: int = 40000):
        self.headless = headless
        self.timeout = timeout
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name (e.g., 'blinkit', 'zepto')."""
        pass
    
    @abstractmethod
    def get_platform_url(self) -> str:
        """Return the platform's base URL."""
        pass
    
    @abstractmethod
    def set_location(self, page, address: str):
        """Set location on the platform's website."""
        pass
    
    @abstractmethod
    def extract_eta(self, page) -> str:
        """Extract ETA from the page."""
        pass
    
    def normalize_eta(self, raw: str) -> str:
        """Clean raw ETA text like 'Delivery in 12 min' -> '12 min'."""
        if not raw:
            return "N/A"
        raw = raw.strip().lower()
        
        # Look for 'X min' pattern
        m = re.search(r'(\d+)\s*min', raw)
        if m:
            return f"{m.group(1)} min"
        
        # Look for any number
        m = re.search(r'(\d+)', raw)
        if m:
            return f"{m.group(1)} min"
        
        return "Store Unavailable / Closed"
    
    def create_browser_context(self, playwright):
        """Create a browser context with standard settings."""
        browser = playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        
        context = browser.new_context(
            user_agent=self.DEFAULT_UA,
            viewport=self.DEFAULT_VIEWPORT,
            locale=self.DEFAULT_LOCALE,
            timezone_id=self.DEFAULT_TIMEZONE,
        )
        
        # Block images and fonts for faster loading
        context.route("**/*", lambda route: (
            route.abort() if route.request.resource_type in ["image", "font"] else route.continue_()
        ))
        
        return browser, context
    
    def get_eta(self, address: str) -> str:
        """Main method to fetch ETA for a given address."""
        with sync_playwright() as p:
            browser, context = self.create_browser_context(p)
            page = context.new_page()
            eta = "N/A"
            
            try:
                # Navigate to platform
                page.goto(self.get_platform_url(), timeout=self.timeout)
                
                # Set location using platform-specific logic
                self.set_location(page, address)
                
                # Extract ETA using platform-specific logic
                raw_eta = self.extract_eta(page)
                eta = self.normalize_eta(raw_eta)
                
                print(f"✅ {self.get_platform_name()} ETA: {eta}")
                
            except Exception as e:
                print(f"❌ Error fetching {self.get_platform_name()} ETA: {e}")
                eta = "N/A"
            finally:
                browser.close()
            
            return eta