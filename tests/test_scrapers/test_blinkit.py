"""
Tests for Blinkit scraper functionality.
"""

import sys
import os
import pytest

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.scrapers.blinkit import BlinkitScraper, run_scraper


class TestBlinkitScraper:
    """Test cases for Blinkit scraper."""
    
    def test_scraper_initialization(self):
        """Test that scraper can be initialized."""
        scraper = BlinkitScraper()
        assert scraper.get_platform_name() == "blinkit"
        assert scraper.headless is True
    
    def test_build_search_url(self):
        """Test URL building functionality."""
        scraper = BlinkitScraper()
        url = scraper.build_search_url("milk")
        assert "blinkit.com" in url
        assert "milk" in url
        
        # Test with spaces
        url = scraper.build_search_url("amul milk")
        assert "amul%20milk" in url
    
    def test_legacy_function_compatibility(self):
        """Test that legacy functions still work."""
        # This should not raise an exception
        from src.scrapers.blinkit import product_key, is_complete
        
        test_item = {
            "name": "Test Product",
            "price": "₹100",
            "product_url": "https://example.com/product"
        }
        
        assert product_key(test_item) == "https://example.com/product"
        assert is_complete(test_item) is True
        
        # Test incomplete item
        incomplete_item = {"name": "Test"}
        assert is_complete(incomplete_item) is False
    
    @pytest.mark.slow
    def test_scraper_with_real_search(self):
        """Test scraper with real search (marked as slow test)."""
        # This test actually hits the Blinkit website
        # Skip in CI or when running quick tests
        scraper = BlinkitScraper(headless=True)
        results = scraper.scrape("milk")
        
        # Should return a list (even if empty)
        assert isinstance(results, list)
        
        # If we get results, they should have the expected structure
        if results:
            item = results[0]
            assert "platform" in item
            assert "name" in item
            assert item["platform"] == "blinkit"


if __name__ == "__main__":
    # Run basic tests
    test_class = TestBlinkitScraper()
    
    try:
        test_class.test_scraper_initialization()
        print("✅ Scraper initialization test passed")
        
        test_class.test_build_search_url()
        print("✅ URL building test passed")
        
        test_class.test_legacy_function_compatibility()
        print("✅ Legacy compatibility test passed")
        
        print("🎉 All basic tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)