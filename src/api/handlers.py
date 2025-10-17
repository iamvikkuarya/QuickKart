"""
Business logic handlers for QuickCompare API operations.
"""

import time
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Tuple

# Import scrapers
from ..scrapers.blinkit import run_scraper
from ..scrapers.zepto import run_zepto_scraper
from ..scrapers.dmart import run_dmart_scraper

# Import ETA services
from ..eta.blinkit import get_blinkit_eta
from ..eta.zepto import get_zepto_eta
from ..eta.dmart import get_dmart_eta

# Import core services
from ..core.database import save_products
from ..core.utils import merge_products
from ..core.cache import search_cache, eta_cache
from ..models.location import get_store_details
from ..models.product import SearchRequest, ETARequest, ETAResponse


class ConfigHandler:
    """Handler for configuration-related operations."""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get application configuration."""
        return {
            "maps_api_key": os.getenv("GOOGLE_MAPS_API_KEY")
        }


class SearchHandler:
    """Handler for product search operations."""
    
    def __init__(self, debug: bool = True):
        self.debug = debug
    
    def search_products(self, request_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Handle product search request.
        Returns (results, status_code).
        """
        # Parse and validate request
        try:
            search_request = SearchRequest.from_dict(request_data)
        except Exception as e:
            return {"error": f"Invalid request: {e}"}, 400
        
        if not search_request.query:
            return {"error": "Missing query"}, 400
        
        # Set defaults
        address = search_request.address if search_request.address else "Kothrud, Pune"
        pincode = search_request.pincode if search_request.pincode else "411038"
        
        print(f"📦 Received: query={search_request.query}")
        
        # Check cache
        cached_result = search_cache.get_search_results(search_request.query, address, pincode)
        if cached_result:
            print(f"✅ Serving cached result")
            return cached_result, 200
        
        print(f"🔄 Scraping fresh data for '{search_request.query}' at {address} ({pincode})")
        
        # Execute scrapers concurrently
        results = self._scrape_all_platforms(search_request.query, pincode)
        
        if not results:
            print("⚠️ No results scraped from any platform")
        
        # Save to database
        save_products(results)
        
        # Debug output
        if self.debug:
            self._debug_raw_results(results)
        
        # Merge products
        merged_results = merge_products(results)
        
        # Debug merged output
        if self.debug:
            self._debug_merged_results(merged_results)
        
        # Cache results
        search_cache.set_search_results(search_request.query, address, pincode, merged_results)
        
        return merged_results, 200
    
    def _scrape_all_platforms(self, query: str, pincode: str) -> List[Dict[str, Any]]:
        """Scrape all platforms concurrently."""
        results = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit scraper tasks (use head mode if debugging)
            headless_mode = not self.debug  # Show browser if debug=True
            fut_blinkit = executor.submit(run_scraper, query, headless_mode)
            fut_zepto = executor.submit(run_zepto_scraper, query, headless_mode)
            
            # Get DMart store details
            unique_id, store_id = get_store_details(pincode)
            fut_dmart = executor.submit(run_dmart_scraper, query, store_id) if store_id else None
            
            # Collect results
            self._collect_scraper_result(fut_blinkit, "Blinkit", "🟢", results)
            self._collect_scraper_result(fut_zepto, "Zepto", "🟣", results)
            
            if fut_dmart:
                self._collect_scraper_result(fut_dmart, "Dmart", "🟡", results)
        
        return results
    
    def _collect_scraper_result(self, future, platform_name: str, emoji: str, results: List):
        """Collect result from a scraper future."""
        try:
            platform_results = future.result() or []
            results.extend(platform_results)
            print(f"{emoji} {platform_name} returned {len(platform_results)} items")
        except Exception as e:
            print(f"⚠️ {platform_name} scraper error: {e}")
    
    def _debug_raw_results(self, results: List[Dict[str, Any]]):
        """Print debug information for raw scraper results."""
        print("\n🔍 DEBUG: Raw scraper output")
        for r in results:
            print(f"   {r['platform']} → {r['name']} | {repr(r['quantity'])}")
    
    def _debug_merged_results(self, merged_results: List[Dict[str, Any]]):
        """Print debug information for merged results."""
        print("\n📦 DEBUG: Merged output")
        for m in merged_results:
            print(f"- {m['name']} ({m['quantity']})")
            for p in m['platforms']:
                print(f"   • {p['platform']}: {p['price']} ({p['delivery_time']})")


class ETAHandler:
    """Handler for ETA-related operations."""
    
    def get_eta(self, request_data: Dict[str, Any]) -> Tuple[Dict[str, str], int]:
        """
        Handle ETA request.
        Returns (eta_results, status_code).
        """
        # Parse request
        eta_request = ETARequest.from_dict(request_data or {})
        
        # Set defaults
        address = eta_request.address if eta_request.address else "Azad Nagar, Kothrud, Pune"
        pincode = eta_request.pincode if eta_request.pincode else "411038"
        
        # Check cache
        cached_eta = eta_cache.get_eta(address, pincode)
        if cached_eta:
            return cached_eta, 200
        
        # Fetch ETA from all platforms
        eta_response = self._fetch_all_etas(address, pincode)
        
        # Cache results
        eta_results = eta_response.to_dict()
        eta_cache.set_eta(address, pincode, eta_results)
        
        return eta_results, 200
    
    def _fetch_all_etas(self, address: str, pincode: str) -> ETAResponse:
        """Fetch ETA from all platforms concurrently."""
        eta_response = ETAResponse()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit ETA tasks
            fut_blinkit = executor.submit(get_blinkit_eta, address)
            fut_zepto = executor.submit(get_zepto_eta, address)
            fut_dmart = executor.submit(get_dmart_eta, pincode)  # Use pincode for DMart
            
            # Collect results
            try:
                eta_response.blinkit = fut_blinkit.result(timeout=25) or "N/A"
            except Exception as e:
                print("ETA blinkit error:", e)
            
            try:
                eta_response.zepto = fut_zepto.result(timeout=25) or "N/A"
            except Exception as e:
                print("ETA zepto error:", e)
            
            try:
                eta_response.dmart = fut_dmart.result(timeout=25) or "N/A"
            except Exception as e:
                print("ETA dmart error:", e)
        
        return eta_response


class StaticHandler:
    """Handler for static file operations."""
    
    @staticmethod
    def serve_home():
        """Serve the home page."""
        # This will be handled by the Flask app's send_static_file
        return "static/index.html"