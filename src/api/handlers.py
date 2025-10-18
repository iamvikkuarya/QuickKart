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
        self.suggestions_handler = ProductSuggestionsHandler()
    
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
        
        # Save search query to suggestions
        self.suggestions_handler.add_search_query(search_request.query)
        
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
        
        # Save product names for suggestions
        self.suggestions_handler.add_product_suggestions(results)
        
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


class ProductSuggestionsHandler:
    """Handler for product suggestions operations."""
    
    def __init__(self):
        self.suggestions_file = "data/product_suggestions.txt"
        self.max_suggestions = 1000  # Limit to prevent file from growing too large
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists."""
        import os
        os.makedirs(os.path.dirname(self.suggestions_file), exist_ok=True)
    
    def get_product_suggestions(self) -> Tuple[Dict[str, Any], int]:
        """Get all product suggestions."""
        try:
            suggestions = self._load_suggestions()
            # Clean up file if we detect duplicates during load
            self._cleanup_duplicates_if_needed(suggestions)
            return {"products": suggestions}, 200
        except Exception as e:
            print(f"Error loading product suggestions: {e}")
            return {"products": []}, 200
    
    def _cleanup_duplicates_if_needed(self, loaded_suggestions: List[str]):
        """Clean up duplicates if the loaded suggestions contain them."""
        try:
            # Check if we need cleanup by comparing original count vs unique count
            unique_normalized = set()
            unique_suggestions = []
            
            for suggestion in loaded_suggestions:
                normalized = self._normalize_for_comparison(suggestion)
                if normalized and normalized not in unique_normalized:
                    unique_suggestions.append(suggestion)
                    unique_normalized.add(normalized)
            
            # If we found duplicates, clean up the file
            if len(unique_suggestions) < len(loaded_suggestions):
                print(f"🧹 Cleaning up {len(loaded_suggestions) - len(unique_suggestions)} duplicate suggestions")
                self._save_suggestions(unique_suggestions)
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def add_search_query(self, query: str):
        """Add user search query to suggestions."""
        try:
            if not query or len(query.strip()) < 2:
                return
            
            # Clean the search query (keep it simple)
            cleaned_query = query.strip().lower()
            if not cleaned_query or len(cleaned_query) < 2:
                return
            
            existing_suggestions = set(self._load_suggestions_normalized())
            normalized_query = self._normalize_for_comparison(cleaned_query)
            
            # Only add if it's not already in suggestions
            if normalized_query not in existing_suggestions:
                current_suggestions = self._load_suggestions()
                
                # Add search query with QUERY: prefix to distinguish from product names
                query_entry = f"QUERY:{cleaned_query}"
                current_suggestions.append(query_entry)
                
                # Limit suggestions
                if len(current_suggestions) > self.max_suggestions:
                    current_suggestions = current_suggestions[-self.max_suggestions:]
                
                self._save_suggestions(current_suggestions)
                print(f"🔍 Added search query: '{cleaned_query}'")
            
        except Exception as e:
            print(f"Error adding search query: {e}")
    
    def add_product_suggestions(self, products: List[Dict[str, Any]]):
        """Add new product names from scraping results."""
        try:
            existing_suggestions = set(self._load_suggestions_normalized())
            new_suggestions = set()
            
            # Extract product names from scraping results
            for product in products:
                if isinstance(product, dict) and 'name' in product:
                    # Clean and normalize product name
                    name = self._clean_product_name(product['name'])
                    if name and len(name) > 2:  # Only add meaningful names
                        # Normalize for comparison (lowercase, no extra spaces)
                        normalized_name = self._normalize_for_comparison(name)
                        if normalized_name not in existing_suggestions:
                            new_suggestions.add(name)  # Add original cleaned name
                            existing_suggestions.add(normalized_name)  # Track normalized version
            
            # Only save if we have new suggestions
            if new_suggestions:
                # Load current suggestions and add new ones
                current_suggestions = self._load_suggestions()
                all_suggestions = set(current_suggestions).union(new_suggestions)
                
                # Limit the number of suggestions
                if len(all_suggestions) > self.max_suggestions:
                    # Keep alphabetically sorted suggestions (more predictable than "recent")
                    all_suggestions = sorted(all_suggestions)[:self.max_suggestions]
                else:
                    all_suggestions = list(all_suggestions)
                
                # Save back to file
                self._save_suggestions(all_suggestions)
                
                print(f"📝 Added {len(new_suggestions)} new product suggestions (total: {len(all_suggestions)})")
            else:
                print("📝 No new product suggestions to add")
            
        except Exception as e:
            print(f"Error adding product suggestions: {e}")
    
    def _clean_search_query(self, query: str) -> str:
        """Clean user search query for suggestions."""
        if not query:
            return ""
        
        # Basic cleaning
        query = query.strip().lower()
        
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Only return queries that are reasonable length
        if 2 <= len(query) <= 50:
            return query
        
        return ""
    
    def _load_suggestions_normalized(self) -> set:
        """Load suggestions and return normalized versions for comparison."""
        suggestions = self._load_suggestions()
        return {self._normalize_for_comparison(s) for s in suggestions}
    
    def _normalize_for_comparison(self, name: str) -> str:
        """Normalize name for duplicate comparison."""
        if not name:
            return ""
        # Convert to lowercase, remove extra spaces, and basic punctuation
        normalized = name.lower().strip()
        normalized = ' '.join(normalized.split())  # Remove extra whitespace
        # Remove common punctuation that might cause false duplicates
        normalized = normalized.replace('-', ' ').replace('_', ' ').replace('.', '')
        normalized = ' '.join(normalized.split())  # Clean up spaces again
        return normalized
    
    def _load_suggestions(self) -> List[str]:
        """Load suggestions from file."""
        try:
            if os.path.exists(self.suggestions_file):
                with open(self.suggestions_file, 'r', encoding='utf-8') as f:
                    suggestions = [line.strip() for line in f if line.strip()]
                    # Remove exact duplicates and empty lines
                    unique_suggestions = []
                    seen = set()
                    for suggestion in suggestions:
                        normalized = self._normalize_for_comparison(suggestion)
                        if normalized and normalized not in seen:
                            unique_suggestions.append(suggestion)
                            seen.add(normalized)
                    return unique_suggestions
            return []
        except Exception as e:
            print(f"Error reading suggestions file: {e}")
            return []
    
    def _save_suggestions(self, suggestions: List[str]):
        """Save suggestions to file with strict deduplication."""
        try:
            # Final deduplication before saving
            unique_suggestions = []
            seen_normalized = set()
            
            for suggestion in suggestions:
                if suggestion and suggestion.strip():
                    normalized = self._normalize_for_comparison(suggestion)
                    if normalized and normalized not in seen_normalized:
                        unique_suggestions.append(suggestion.strip())
                        seen_normalized.add(normalized)
            
            # Sort alphabetically for consistent file structure
            unique_suggestions.sort(key=str.lower)
            
            with open(self.suggestions_file, 'w', encoding='utf-8') as f:
                for suggestion in unique_suggestions:
                    f.write(f"{suggestion}\n")
                    
            print(f"💾 Saved {len(unique_suggestions)} unique suggestions to file")
            
        except Exception as e:
            print(f"Error writing suggestions file: {e}")
    
    def _clean_product_name(self, name: str) -> str:
        """Clean and normalize product name for suggestions."""
        if not name:
            return ""
        
        # Basic cleaning
        name = name.strip()
        
        # Remove common prefixes/suffixes that aren't useful for search
        prefixes_to_remove = ['buy ', 'get ', 'order ']
        suffixes_to_remove = [' online', ' delivery', ' - pack of', ' pack']
        
        name_lower = name.lower()
        for prefix in prefixes_to_remove:
            if name_lower.startswith(prefix):
                name = name[len(prefix):]
                break
        
        for suffix in suffixes_to_remove:
            if name_lower.endswith(suffix):
                name = name[:-len(suffix)]
                break
        
        # Remove size/quantity variations to group similar products
        name = self._remove_size_variations(name)
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Only return names that are reasonable length
        if 2 <= len(name) <= 50:
            return name
        
        return ""
    
    def _remove_size_variations(self, name: str) -> str:
        """Remove size/quantity variations from product names."""
        import re
        
        # Patterns to remove size/quantity information
        size_patterns = [
            # Weight patterns: "500g", "1kg", "2.5 kg", "500 gm", "1.5l", "250ml", etc.
            r'\s*:\s*\d+\.?\d*\s*(g|gm|gram|grams|kg|kilogram|kilograms|l|ltr|litre|litres|ml|millilitre|millilitres)\b',
            r'\s*-\s*\d+\.?\d*\s*(g|gm|gram|grams|kg|kilogram|kilograms|l|ltr|litre|litres|ml|millilitre|millilitres)\b',
            r'\s*\(\s*\d+\.?\d*\s*(g|gm|gram|grams|kg|kilogram|kilograms|l|ltr|litre|litres|ml|millilitre|millilitres)\s*\)',
            r'\s+\d+\.?\d*\s*(g|gm|gram|grams|kg|kilogram|kilograms|l|ltr|litre|litres|ml|millilitre|millilitres)\b',
            
            # Count patterns: "pack of 6", "6 pieces", "12 count", etc.
            r'\s*:\s*\d+\s*(pieces?|pcs?|count|pack)\b',
            r'\s*-\s*\d+\s*(pieces?|pcs?|count|pack)\b',
            r'\s*\(\s*\d+\s*(pieces?|pcs?|count|pack)\s*\)',
            r'\s+\d+\s*(pieces?|pcs?|count|pack)\b',
            r'\s*pack\s+of\s+\d+',
            
            # Size descriptors: "small", "medium", "large", "family pack", etc.
            r'\s*-\s*(small|medium|large|xl|xxl|family\s+pack|economy\s+pack|jumbo|mini)\b',
            r'\s*\(\s*(small|medium|large|xl|xxl|family\s+pack|economy\s+pack|jumbo|mini)\s*\)',
            r'\s+(small|medium|large|xl|xxl|family\s+pack|economy\s+pack|jumbo|mini)\b',
            
            # Generic size patterns: ": 250 g", "- 1L", "(500ml)", etc.
            r'\s*:\s*\d+\.?\d*\s*[a-zA-Z]*\b',
            r'\s*-\s*\d+\.?\d*\s*[a-zA-Z]*\b',
            r'\s*\(\s*\d+\.?\d*\s*[a-zA-Z]*\s*\)',
        ]
        
        cleaned_name = name
        for pattern in size_patterns:
            cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE)
        
        # Clean up any double spaces or trailing/leading spaces
        cleaned_name = ' '.join(cleaned_name.split())
        
        return cleaned_name


class StaticHandler:
    """Handler for static file operations."""
    
    @staticmethod
    def serve_home():
        """Serve the home page."""
        # This will be handled by the Flask app's send_static_file
        return "static/index.html"