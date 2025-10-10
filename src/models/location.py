"""
Location services for store lookup and management.
"""

import requests
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class StoreInfo:
    """Store information for a location."""
    unique_id: str
    store_id: str
    pincode: str
    address: str = ""
    
    def is_valid(self) -> bool:
        """Check if store info has required data."""
        return bool(self.unique_id and self.store_id)


class LocationService:
    """Service for handling location-based operations."""
    
    # Shared headers for all DMart API calls
    BASE_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/117.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.dmart.in",
        "Referer": "https://www.dmart.in/",
    }
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._store_cache: Dict[str, StoreInfo] = {}
    
    def get_unique_id(self, pincode: str) -> str:
        """Step 1: Get uniqueId for a given pincode."""
        url = "https://digital.dmart.in/api/v2/pincodes/suggestions"
        try:
            resp = requests.post(
                url, 
                json={"searchText": pincode}, 
                headers=self.BASE_HEADERS, 
                timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()
            
            results = data.get("searchResult", [])
            return results[0]["uniqueId"] if results else ""
        except Exception as e:
            print(f"⚠️ Error getting unique_id for {pincode}: {e}")
            return ""
    
    def get_store_id(self, pincode: str, unique_id: str) -> str:
        """Step 2: Get storeId using uniqueId + pincode."""
        url = "https://digital.dmart.in/api/v2/pincodes/details"
        payload = {
            "uniqueId": unique_id,
            "apiMode": "GA",
            "pincode": pincode,
            "currentLat": "",
            "currentLng": "",
        }
        try:
            resp = requests.post(url, json=payload, headers=self.BASE_HEADERS, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            
            return str(data.get("storePincodeDetails", {}).get("storeId", ""))
        except Exception as e:
            print(f"⚠️ Error getting store_id for {pincode}: {e}")
            return ""
    
    def get_store_info(self, pincode: str, use_cache: bool = True) -> StoreInfo:
        """
        Main function: resolve pincode → StoreInfo.
        Returns StoreInfo object with unique_id and store_id.
        """
        # Check cache first
        if use_cache and pincode in self._store_cache:
            return self._store_cache[pincode]
        
        unique_id = self.get_unique_id(pincode)
        if not unique_id:
            store_info = StoreInfo(unique_id="", store_id="", pincode=pincode)
        else:
            store_id = self.get_store_id(pincode, unique_id)
            store_info = StoreInfo(
                unique_id=unique_id,
                store_id=store_id,
                pincode=pincode
            )
        
        # Cache the result
        if use_cache:
            self._store_cache[pincode] = store_info
        
        return store_info
    
    def get_store_details(self, pincode: str) -> Tuple[str, str]:
        """
        Legacy function: resolve pincode → (uniqueId, storeId).
        Returns (unique_id, store_id) or ("", "") if not found.
        """
        store_info = self.get_store_info(pincode)
        return store_info.unique_id, store_info.store_id
    
    def clear_cache(self) -> None:
        """Clear the store cache."""
        self._store_cache.clear()
    
    def cache_size(self) -> int:
        """Get current cache size."""
        return len(self._store_cache)


class GeolocationService:
    """Service for handling geolocation operations."""
    
    @staticmethod
    def parse_coordinates(data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        """Parse latitude and longitude from request data."""
        try:
            lat = data.get("latitude")
            lng = data.get("longitude")
            
            if lat is not None and lng is not None:
                return float(lat), float(lng)
        except (ValueError, TypeError):
            pass
        
        return None, None
    
    @staticmethod
    def format_address(address: str, pincode: str = "") -> str:
        """Format address with optional pincode."""
        address = address.strip()
        pincode = pincode.strip()
        
        if pincode and pincode not in address:
            return f"{address}, {pincode}"
        return address
    
    @staticmethod
    def extract_pincode_from_address(address: str) -> Optional[str]:
        """Extract pincode from address string using regex."""
        import re
        
        # Look for 6-digit Indian pincode
        match = re.search(r'\b(\d{6})\b', address)
        return match.group(1) if match else None


# Global instance for backward compatibility
_location_service = LocationService()

# Legacy functions for backward compatibility
BASE_HEADERS = _location_service.BASE_HEADERS

def get_unique_id(pincode: str) -> str:
    """Legacy function for backward compatibility."""
    return _location_service.get_unique_id(pincode)

def get_store_id(pincode: str, unique_id: str) -> str:
    """Legacy function for backward compatibility.""" 
    return _location_service.get_store_id(pincode, unique_id)

def get_store_details(pincode: str) -> Tuple[str, str]:
    """Legacy function for backward compatibility."""
    return _location_service.get_store_details(pincode)


if __name__ == "__main__":
    # Quick test
    service = LocationService()
    pin = "411038"
    store_info = service.get_store_info(pin)
    print(f"✅ For pincode {pin}: uniqueId={store_info.unique_id}, storeId={store_info.store_id}")
    
    # Test legacy function
    uid, sid = get_store_details(pin)
    print(f"✅ Legacy function: uniqueId={uid}, storeId={sid}")