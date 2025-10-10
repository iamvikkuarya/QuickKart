"""
Blinkit platform ETA fetcher implementation.
"""

from .base import BaseETA


class BlinkitETA(BaseETA):
    """ETA fetcher implementation for Blinkit platform."""
    
    def get_platform_name(self) -> str:
        return "blinkit"
    
    def get_platform_url(self) -> str:
        return "https://blinkit.com/"
    
    def set_location(self, page, address: str):
        """Set location on Blinkit."""
        # Step 1: type into location search box
        search_box = page.locator('input[name="select-locality"]').first
        search_box.fill(address)
        page.wait_for_timeout(800)  # let suggestions appear
        
        # Step 2: click first suggestion
        suggestion = page.locator(
            "#app > div > div > div.containers__HeaderContainer-sc-1t9i1pe-0.jNcsdt "
            "> header > div.LocationDropDown__LocationModalContainer-sc-bx29pc-0.hxA-Dsy "
            "> div.location__shake-container-v1.animated > div > div > div.location-footer "
            "> div > div > div:nth-child(1)"
        )
        suggestion.click(timeout=5000)
        
        # Step 3: small wait for page to refresh ETA
        page.wait_for_timeout(2000)
    
    def extract_eta(self, page) -> str:
        """Extract ETA from Blinkit page."""
        raw = ""
        
        # Step 4: poll for ETA until available (max ~5s)
        for _ in range(5):
            for sel in [
                "[data-testid='delivery-time']",
                "div.LocationBar__Title-sc-x8ezho-8",
                ":text('min')",
            ]:
                el = page.locator(sel).first
                if el.count():
                    txt = (el.inner_text() or "").strip()
                    if txt:
                        raw = txt
                        break
            if raw:
                break
            page.wait_for_timeout(1000)
        
        return raw


# Factory function to maintain backward compatibility
def get_blinkit_eta(address: str, headed: bool = False) -> str:
    """Legacy function for backward compatibility."""
    eta_fetcher = BlinkitETA(headless=not headed)
    return eta_fetcher.get_eta(address)


# Legacy function for backward compatibility
def normalize_eta(raw: str) -> str:
    """Legacy function for backward compatibility."""
    eta_fetcher = BlinkitETA()
    return eta_fetcher.normalize_eta(raw)


if __name__ == "__main__":
    eta_fetcher = BlinkitETA(headless=False)  # Set to True for production
    result = eta_fetcher.get_eta("Azad Nagar, Kothrud")
    print("Blinkit ETA:", result)