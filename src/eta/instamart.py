"""
Instamart platform ETA fetcher implementation.
"""

from playwright.sync_api import TimeoutError
from .base import BaseETA


class InstamartETA(BaseETA):
    """ETA fetcher implementation for Instamart platform."""
    
    def __init__(self, latitude: float = 18.5026501, longitude: float = 73.8073136, **kwargs):
        super().__init__(**kwargs)
        self.latitude = latitude
        self.longitude = longitude
    
    def get_platform_name(self) -> str:
        return "instamart"
    
    def get_platform_url(self) -> str:
        return "https://www.swiggy.com/instamart"
    
    def create_browser_context(self, playwright):
        """Create a browser context with geolocation for Instamart."""
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
            geolocation={"latitude": self.latitude, "longitude": self.longitude},
            permissions=["geolocation"],
            locale=self.DEFAULT_LOCALE,
            timezone_id=self.DEFAULT_TIMEZONE,
        )
        
        context.add_init_script(
            'Object.defineProperty(navigator, "webdriver", { get: () => undefined });'
        )
        
        return browser, context
    
    def set_location(self, page, address: str = None):
        """Set location on Instamart using GPS."""
        try:
            page.locator('div[data-testid="set-gps-button"]').click(timeout=8000)
        except TimeoutError:
            print("⚠️ 'Use current location' not found, relying on injected geolocation.")
    
    def extract_eta(self, page) -> str:
        """Extract ETA from Instamart page."""
        return self._extract_eta_with_retry(page, ["._2AY8J"])
    
    def _extract_eta_with_retry(self, page, candidates: list, retries: int = 3, delay: int = 800) -> str:
        """Extract ETA with retry logic."""
        for _ in range(retries):
            for sel in candidates:
                try:
                    el = page.locator(sel).first
                    if el.count():
                        txt = (el.inner_text() or "").strip()
                        if txt:
                            return self.normalize_eta(txt)
                except Exception:
                    continue
            page.wait_for_timeout(delay)
        return "N/A"


def get_eta_with_location(latitude: float = 18.5026501, longitude: float = 73.8073136) -> str:
    """Get ETA with custom location coordinates."""
    eta_fetcher = InstamartETA(latitude=latitude, longitude=longitude)
    return eta_fetcher.get_eta("")  # Address not used for Instamart, uses GPS


# Factory function to maintain backward compatibility
def get_instamart_eta(latitude: float = 18.5026501, longitude: float = 73.8073136, headed: bool = False) -> str:
    """Legacy function for backward compatibility."""
    eta_fetcher = InstamartETA(latitude=latitude, longitude=longitude, headless=not headed)
    return eta_fetcher.get_eta("")


# Legacy function for backward compatibility
def normalize_eta(raw: str) -> str:
    """Legacy function for backward compatibility."""
    eta_fetcher = InstamartETA()
    return eta_fetcher.normalize_eta(raw)


if __name__ == "__main__":
    eta_fetcher = InstamartETA(headless=False)  # Set to True for production
    result = eta_fetcher.get_eta("")
    print("Instamart ETA:", result)