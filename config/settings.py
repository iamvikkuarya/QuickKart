"""
Centralized configuration management for QuickCompare.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration."""
    name: str = "product.db"
    timeout: int = 30
    
    @property
    def connection_string(self) -> str:
        return self.name


@dataclass
class CacheConfig:
    """Cache configuration."""
    default_ttl: int = 300  # 5 minutes
    search_ttl: int = 300   # 5 minutes  
    eta_ttl: int = 300      # 5 minutes
    cleanup_interval: int = 3600  # 1 hour


@dataclass
class ScrapingConfig:
    """Web scraping configuration."""
    timeout: int = 40000
    headless: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    max_workers: int = 3
    
    # Platform-specific settings
    blinkit_scroll_count: int = 3
    zepto_scroll_count: int = 3
    instamart_scroll_count: int = 4
    
    # Default coordinates for location-based services
    default_latitude: float = 18.5204
    default_longitude: float = 73.8567


@dataclass
class APIConfig:
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    
    # Rate limiting
    rate_limit_enabled: bool = False
    requests_per_minute: int = 60
    
    # CORS settings
    cors_enabled: bool = True
    cors_origins: str = "*"


@dataclass
class LocationConfig:
    """Location services configuration."""
    default_address: str = "Kothrud, Pune"
    default_pincode: str = "411038"
    default_area: str = "Azad Nagar, Kothrud, Pune"
    
    # Geolocation defaults
    default_latitude: float = 18.5204
    default_longitude: float = 73.8567
    
    # Cache settings for location lookups
    location_cache_ttl: int = 3600  # 1 hour


@dataclass
class ExternalServicesConfig:
    """Configuration for external services."""
    google_maps_api_key: Optional[str] = None
    
    # Request timeouts
    dmart_api_timeout: int = 10
    eta_request_timeout: int = 25
    
    # User agents
    default_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )


class AppConfig:
    """Main application configuration class."""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('FLASK_ENV', 'production')
        self.debug = self.environment == 'development'
        
        # Load configurations
        self.database = DatabaseConfig()
        self.cache = CacheConfig()
        self.scraping = ScrapingConfig()
        self.api = APIConfig()
        self.location = LocationConfig()
        self.external_services = ExternalServicesConfig()
        
        # Apply environment-specific overrides
        self._apply_environment_overrides()
        self._load_from_environment()
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides."""
        if self.environment == 'development':
            self.api.debug = True
            self.api.host = "127.0.0.1"
            self.scraping.headless = False  # Show browser in dev mode
            self.cache.default_ttl = 60  # Shorter cache in dev
        
        elif self.environment == 'testing':
            self.database.name = "test_product.db"
            self.cache.default_ttl = 10  # Very short cache for tests
            self.scraping.headless = True
            self.api.debug = False
        
        elif self.environment == 'production':
            self.api.debug = False
            self.api.host = "0.0.0.0"
            self.scraping.headless = True
            self.cache.default_ttl = 300  # 5 minutes
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # API settings
        self.api.port = int(os.getenv('PORT', self.api.port))
        self.api.host = os.getenv('HOST', self.api.host)
        self.api.debug = os.getenv('FLASK_DEBUG', '').lower() in ('true', '1', 'yes')
        
        # Database settings
        db_name = os.getenv('DATABASE_NAME')
        if db_name:
            self.database.name = db_name
        
        # External services
        self.external_services.google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        
        # Cache settings
        cache_ttl = os.getenv('CACHE_TTL')
        if cache_ttl:
            try:
                self.cache.default_ttl = int(cache_ttl)
                self.cache.search_ttl = int(cache_ttl)
                self.cache.eta_ttl = int(cache_ttl)
            except ValueError:
                pass
        
        # Location settings
        default_pincode = os.getenv('DEFAULT_PINCODE')
        if default_pincode:
            self.location.default_pincode = default_pincode
        
        default_address = os.getenv('DEFAULT_ADDRESS')
        if default_address:
            self.location.default_address = default_address
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'environment': self.environment,
            'debug': self.debug,
            'database': {
                'name': self.database.name,
                'timeout': self.database.timeout,
            },
            'cache': {
                'default_ttl': self.cache.default_ttl,
                'search_ttl': self.cache.search_ttl,
                'eta_ttl': self.cache.eta_ttl,
            },
            'api': {
                'host': self.api.host,
                'port': self.api.port,
                'debug': self.api.debug,
            },
            'scraping': {
                'timeout': self.scraping.timeout,
                'headless': self.scraping.headless,
                'max_workers': self.scraping.max_workers,
            },
            'location': {
                'default_address': self.location.default_address,
                'default_pincode': self.location.default_pincode,
            }
        }
    
    def get_maps_api_key(self) -> Optional[str]:
        """Get Google Maps API key."""
        return self.external_services.google_maps_api_key
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == 'development'
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == 'production'


# Global configuration instance
config = AppConfig()


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    return config


def reload_config():
    """Reload configuration from environment."""
    global config
    config = AppConfig()
    return config