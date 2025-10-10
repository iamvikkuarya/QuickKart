"""
Product data models for QuickCompare application.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum


class Platform(Enum):
    """Supported platforms."""
    BLINKIT = "blinkit"
    ZEPTO = "zepto"
    DMART = "dmart"
    INSTAMART = "instamart"


@dataclass
class ProductInfo:
    """Individual product information from a platform."""
    platform: str
    name: str
    price: str
    quantity: str
    image_url: str
    product_url: str
    delivery_time: str = "N/A"
    in_stock: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductInfo':
        """Create ProductInfo from dictionary."""
        return cls(
            platform=data.get("platform", ""),
            name=data.get("name", ""),
            price=data.get("price", "N/A"),
            quantity=data.get("quantity", "N/A"),
            image_url=data.get("image_url", ""),
            product_url=data.get("product_url", ""),
            delivery_time=data.get("delivery_time", "N/A"),
            in_stock=data.get("in_stock", True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ProductInfo to dictionary."""
        return {
            "platform": self.platform,
            "name": self.name,
            "price": self.price,
            "quantity": self.quantity,
            "image_url": self.image_url,
            "product_url": self.product_url,
            "delivery_time": self.delivery_time,
            "in_stock": self.in_stock
        }


@dataclass
class PlatformProduct:
    """Product offering from a specific platform."""
    platform: str
    price: str
    delivery_time: str
    product_url: str
    image_url: str
    in_stock: bool = True
    
    @classmethod
    def from_product_info(cls, product: ProductInfo) -> 'PlatformProduct':
        """Create PlatformProduct from ProductInfo."""
        return cls(
            platform=product.platform,
            price=product.price,
            delivery_time=product.delivery_time,
            product_url=product.product_url,
            image_url=product.image_url,
            in_stock=product.in_stock
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PlatformProduct to dictionary."""
        return {
            "platform": self.platform,
            "price": self.price,
            "delivery_time": self.delivery_time,
            "product_url": self.product_url,
            "image_url": self.image_url,
            "in_stock": self.in_stock
        }


@dataclass
class MergedProduct:
    """Merged product from multiple platforms."""
    name: str
    quantity: str
    image_url: str
    platforms: List[PlatformProduct]
    
    @classmethod
    def from_single_product(cls, product: ProductInfo) -> 'MergedProduct':
        """Create MergedProduct from a single ProductInfo."""
        return cls(
            name=product.name,
            quantity=product.quantity,
            image_url=product.image_url,
            platforms=[PlatformProduct.from_product_info(product)]
        )
    
    def add_platform(self, product: ProductInfo) -> None:
        """Add another platform to this merged product."""
        platform_product = PlatformProduct.from_product_info(product)
        self.platforms.append(platform_product)
    
    def has_platform(self, platform_name: str) -> bool:
        """Check if this product has a specific platform."""
        return any(p.platform == platform_name for p in self.platforms)
    
    def get_platform(self, platform_name: str) -> Optional[PlatformProduct]:
        """Get specific platform data."""
        for platform in self.platforms:
            if platform.platform == platform_name:
                return platform
        return None
    
    def get_lowest_price(self) -> Optional[str]:
        """Get the lowest price among all platforms."""
        prices = []
        for platform in self.platforms:
            try:
                # Extract numeric value from price string like "₹123"
                price_str = platform.price.replace("₹", "").replace(",", "").strip()
                if price_str and price_str != "N/A":
                    prices.append(float(price_str))
            except (ValueError, AttributeError):
                continue
        
        if prices:
            lowest = min(prices)
            return f"₹{int(lowest)}"
        return None
    
    def get_fastest_delivery(self) -> Optional[str]:
        """Get the fastest delivery time among all platforms."""
        times = []
        for platform in self.platforms:
            delivery = platform.delivery_time
            if delivery and delivery != "N/A":
                # Extract minutes from strings like "12 min"
                try:
                    import re
                    match = re.search(r'(\d+)', delivery)
                    if match:
                        times.append((int(match.group(1)), delivery))
                except (ValueError, AttributeError):
                    continue
        
        if times:
            times.sort(key=lambda x: x[0])
            return times[0][1]
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert MergedProduct to dictionary."""
        return {
            "name": self.name,
            "quantity": self.quantity,
            "image_url": self.image_url,
            "platforms": [p.to_dict() for p in self.platforms],
            "lowest_price": self.get_lowest_price(),
            "fastest_delivery": self.get_fastest_delivery()
        }


@dataclass
class SearchRequest:
    """Search request parameters."""
    query: str
    address: str = ""
    pincode: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchRequest':
        """Create SearchRequest from dictionary."""
        return cls(
            query=data.get("query", "").strip().lower(),
            address=data.get("address", "").strip(),
            pincode=data.get("pincode", "").strip(),
            latitude=data.get("latitude"),
            longitude=data.get("longitude")
        )


@dataclass
class ETARequest:
    """ETA request parameters."""
    address: str
    pincode: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ETARequest':
        """Create ETARequest from dictionary."""
        return cls(
            address=data.get("address", "").strip(),
            pincode=data.get("pincode", "").strip(),
            latitude=data.get("latitude"),
            longitude=data.get("longitude")
        )


@dataclass
class ETAResponse:
    """ETA response from all platforms."""
    blinkit: str = "N/A"
    zepto: str = "N/A"
    dmart: str = "N/A"
    instamart: str = "N/A"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert ETAResponse to dictionary."""
        return {
            "blinkit": self.blinkit,
            "zepto": self.zepto,
            "dmart": self.dmart,
            "instamart": self.instamart
        }