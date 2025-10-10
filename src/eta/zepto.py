"""
Zepto platform ETA fetcher implementation.
"""

from .base import BaseETA


class ZeptoETA(BaseETA):
    """ETA fetcher implementation for Zepto platform."""
    
    def get_platform_name(self) -> str:
        return "zepto"
    
    def get_platform_url(self) -> str:
        return "https://www.zeptonow.com/"
    
    def set_location(self, page, address: str):
        """Set location on Zepto."""
        # Open location selector
        page.click('button[aria-label="Select Location"]', timeout=15000)
        page.fill('div[data-testid="address-search-input"] input', address)
        page.click('div[data-testid="address-search-item"]', timeout=20000)
        page.click('button[data-testid="location-confirm-btn"]', timeout=15000)
        
        # Wait for hydration + slight scroll
        page.wait_for_timeout(800)
        page.evaluate("window.scrollBy(0,300)")
    
    def extract_eta(self, page) -> str:
        """Extract ETA from Zepto page."""
        raw = ""
        
        for sel in [
            "[data-testid='delivery-time']",
            "span.font-extrabold",
            ":text('min')",
        ]:
            el = page.locator(sel).first
            if el.count():
                raw = el.inner_text().strip()
                break
        
        return raw


# Factory function to maintain backward compatibility
def get_zepto_eta(address: str, headed: bool = False) -> str:
    """Legacy function for backward compatibility."""
    eta_fetcher = ZeptoETA(headless=not headed)
    return eta_fetcher.get_eta(address)


# Legacy function for backward compatibility
def normalize_eta(raw: str) -> str:
    """Legacy function for backward compatibility."""
    eta_fetcher = ZeptoETA()
    return eta_fetcher.normalize_eta(raw)


if __name__ == "__main__":
    eta_fetcher = ZeptoETA(headless=False)  # Set to True for production
    result = eta_fetcher.get_eta("Bavdhan, Pune")
    print("Zepto ETA:", result)