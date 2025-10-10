"""
Cache management module for QuickCompare application.
"""

import time
from typing import Any, Optional, Dict, Tuple
from threading import Lock


class CacheManager:
    """Thread-safe cache manager with TTL (Time To Live) support."""
    
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self._lock:
            if key not in self._cache:
                return None
            
            timestamp, value = self._cache[key]
            if time.time() - timestamp > self.default_ttl:
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL override."""
        with self._lock:
            self._cache[key] = (time.time(), value)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache. Returns True if key existed."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns number of entries removed."""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, (timestamp, _) in self._cache.items():
                if current_time - timestamp > self.default_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
        
        return len(expired_keys)
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    def keys(self) -> list:
        """Get all cache keys."""
        with self._lock:
            return list(self._cache.keys())


class SearchCache:
    """Specialized cache for search results."""
    
    def __init__(self, ttl: int = 300):
        self.cache = CacheManager(default_ttl=ttl)
    
    def make_cache_key(self, query: str, address: str, pincode: str) -> str:
        """Generate cache key for search parameters."""
        norm_addr = (address or "").strip().lower()
        norm_pin = (pincode or "").strip()
        return f"search_{query}_{norm_addr}_{norm_pin}"
    
    def get_search_results(self, query: str, address: str, pincode: str) -> Optional[Any]:
        """Get cached search results."""
        key = self.make_cache_key(query, address, pincode)
        return self.cache.get(key)
    
    def set_search_results(self, query: str, address: str, pincode: str, results: Any) -> None:
        """Cache search results."""
        key = self.make_cache_key(query, address, pincode)
        self.cache.set(key, results)


class ETACache:
    """Specialized cache for ETA results."""
    
    def __init__(self, ttl: int = 300):
        self.cache = CacheManager(default_ttl=ttl)
    
    def make_cache_key(self, address: str, pincode: str) -> str:
        """Generate cache key for ETA parameters."""
        norm_addr = (address or "").strip().lower()
        norm_pin = (pincode or "").strip()
        return f"eta_{norm_addr}_{norm_pin}"
    
    def get_eta(self, address: str, pincode: str) -> Optional[Dict[str, str]]:
        """Get cached ETA results."""
        key = self.make_cache_key(address, pincode)
        return self.cache.get(key)
    
    def set_eta(self, address: str, pincode: str, eta_results: Dict[str, str]) -> None:
        """Cache ETA results."""
        key = self.make_cache_key(address, pincode)
        self.cache.set(key, eta_results)


# Global instances for application use
search_cache = SearchCache(ttl=300)  # 5 minutes
eta_cache = ETACache(ttl=300)        # 5 minutes

# Legacy cache dictionaries for backward compatibility
cache = {}
eta_cache_dict = {}

# Legacy cache constants
CACHE_TTL = 300
ETA_CACHE_TTL = 300

# Legacy cache functions for backward compatibility
def make_cache_key(query: str, address: str, pincode: str) -> str:
    """Legacy function for backward compatibility."""
    return search_cache.make_cache_key(query, address, pincode)

def make_eta_cache_key(address: str, pincode: str) -> str:
    """Legacy function for backward compatibility."""
    return eta_cache.make_cache_key(address, pincode)