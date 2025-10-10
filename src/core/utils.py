"""
Utility functions for product processing and matching.
"""

import re
import random
from typing import List, Dict, Any
from rapidfuzz import fuzz


class QuantityNormalizer:
    """Handles quantity normalization and comparison."""
    
    @staticmethod
    def normalize_quantity(qty: str) -> str:
        """Convert all quantity expressions into a standard form like '500ml' or '1kg'."""
        if not qty:
            return ""
        qty = qty.lower().strip()

        # Match patterns like "2 x 500 ml"
        multi = re.match(r"(\d+)\s*[xX]\s*(\d+(?:\.\d+)?)\s*(ml|l|litre|liter|g|kg)", qty)
        if multi:
            count, value, unit = multi.groups()
            total = float(count) * float(value)
            if unit.startswith("l"):
                total *= 1000; unit = "ml"
            if unit.startswith("k"):
                total *= 1000; unit = "g"
            return f"{int(total)}{unit}"

        # Match numbers inside parentheses like "(1 L)" or "(500 ml)"
        paren = re.search(r"\(?(\d+(?:\.\d+)?)\s*(ml|l|litre|liter|g|kg)\)?", qty)
        if paren:
            value, unit = paren.groups()
            total = float(value)
            if unit.startswith("l"):
                total *= 1000; unit = "ml"
            if unit.startswith("k"):
                total *= 1000; unit = "g"
            return f"{int(total)}{unit}"

        # Plain "500 ml"
        match = re.search(r"(\d+(?:\.\d+)?)\s*(ml|l|litre|liter|g|kg)", qty)
        if match:
            value, unit = match.groups()
            total = float(value)
            if unit.startswith("l"):
                total *= 1000; unit = "ml"
            if unit.startswith("k"):
                total *= 1000; unit = "g"
            return f"{int(total)}{unit}"

        return qty.replace(" ", "")
    
    @staticmethod
    def quantities_close(q1: str, q2: str, tolerance: float = 0.15) -> bool:
        """Check if quantities are within tolerance (default 15%)."""
        num_re = re.compile(r"(\d+)(ml|g)")
        m1, m2 = num_re.match(q1 or ""), num_re.match(q2 or "")
        if not (m1 and m2):
            return False
        v1, u1 = int(m1.group(1)), m1.group(2)
        v2, u2 = int(m2.group(1)), m2.group(2)
        if u1 != u2:
            return False
        return abs(v1 - v2) <= tolerance * max(v1, v2)


class ProductProcessor:
    """Handles product name processing and brand extraction."""
    
    # Common noise words to remove from product names
    NOISE_WORDS = [
        "fresh", "pouch", "pack", "pc", "combo", "robusta", "regular",
        "tetra", "homogenised", "homogenized", "standardised", "standardized",
        "long life", "farm", "tub", "cup", "stick", "cone", "bottle", "can",
        "jar", "box", "unit", "sachet", "carton"
    ]
    
    @classmethod
    def extract_brand(cls, name: str) -> str:
        """Extract brand (first word heuristic)."""
        if not name:
            return ""
        return name.strip().split()[0].lower()
    
    @classmethod
    def clean_name(cls, name: str) -> str:
        """Remove packaging/extra words for fuzzy matching."""
        if not name:
            return ""
        name = name.lower()

        for word in cls.NOISE_WORDS:
            name = name.replace(word, "")

        return re.sub(r"\s+", " ", name).strip()


class ProductMerger:
    """Handles merging of products from different platforms."""
    
    def __init__(self, threshold: int = 75, debug: bool = True):
        self.threshold = threshold
        self.debug = debug
        self.quantity_normalizer = QuantityNormalizer()
        self.product_processor = ProductProcessor()
    
    def merge_products(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge products from different platforms based on similarity."""
        merged = []

        for product in results:
            if not product.get("name") or product["name"].strip().lower() in ("", "n/a"):
                continue

            name = product["name"].strip()
            cleaned = self.product_processor.clean_name(name)
            brand = self.product_processor.extract_brand(name)
            quantity = self.quantity_normalizer.normalize_quantity(product.get("quantity", ""))

            matched_group = self._find_matching_group(
                merged, product, cleaned, brand, quantity
            )

            if matched_group:
                self._add_to_group(matched_group, product)
            else:
                self._create_new_group(merged, product, name)

        return self._organize_results(merged)
    
    def _find_matching_group(self, merged: List[Dict], product: Dict, 
                           cleaned: str, brand: str, quantity: str) -> Dict:
        """Find a matching group for the product."""
        for group in merged:
            existing_platforms = {p["platform"] for p in group["platforms"]}
            if product["platform"] in existing_platforms:
                continue

            group_cleaned = self.product_processor.clean_name(group["name"])
            group_brand = self.product_processor.extract_brand(group["name"])
            group_qty = self.quantity_normalizer.normalize_quantity(group["quantity"])

            score = fuzz.token_sort_ratio(cleaned, group_cleaned)
            qty_match = (quantity == group_qty or 
                        self.quantity_normalizer.quantities_close(quantity, group_qty))
            brand_match = (brand == group_brand)

            if self.debug:
                print(
                    f"COMPARE '{cleaned}' vs '{group_cleaned}' "
                    f"→ score={score}, qty={quantity} vs {group_qty}, "
                    f"qty_match={qty_match}, brand_match={brand_match}"
                )

            if ((score >= self.threshold and qty_match and brand_match) or
                (score >= 90 and brand_match)):
                return group

        return None
    
    def _add_to_group(self, group: Dict, product: Dict):
        """Add product to existing group."""
        group["platforms"].append({
            "platform": product["platform"],
            "price": product.get("price", "N/A"),
            "delivery_time": product.get("delivery_time"),
            "product_url": product.get("product_url"),
            "image_url": product.get("image_url"),
            "in_stock": product.get("in_stock", True),
        })
    
    def _create_new_group(self, merged: List, product: Dict, name: str):
        """Create new product group."""
        merged.append({
            "name": name,
            "quantity": product.get("quantity", "N/A"),
            "image_url": product.get("image_url"),
            "platforms": [{
                "platform": product["platform"],
                "price": product.get("price", "N/A"),
                "delivery_time": product.get("delivery_time"),
                "product_url": product.get("product_url"),
                "image_url": product.get("image_url"),
                "in_stock": product.get("in_stock", True),
            }]
        })
    
    def _organize_results(self, merged: List[Dict]) -> List[Dict]:
        """Organize results with merged products first, then shuffled singles."""
        # Split merged vs unmerged
        multi_platform = [m for m in merged if len(m["platforms"]) > 1]
        single_platform = [m for m in merged if len(m["platforms"]) == 1]

        # Shuffle single-platform listings
        random.shuffle(single_platform)

        # Return merged first, shuffled singles after
        return multi_platform + single_platform


# Legacy functions for backward compatibility
def normalize_quantity(qty: str) -> str:
    """Legacy function for backward compatibility."""
    return QuantityNormalizer.normalize_quantity(qty)

def extract_brand(name: str) -> str:
    """Legacy function for backward compatibility."""
    return ProductProcessor.extract_brand(name)

def clean_name(name: str) -> str:
    """Legacy function for backward compatibility."""
    return ProductProcessor.clean_name(name)

def quantities_close(q1: str, q2: str, tolerance: float = 0.15) -> bool:
    """Legacy function for backward compatibility."""
    return QuantityNormalizer.quantities_close(q1, q2, tolerance)

def merge_products(results: List[Dict[str, Any]], threshold: int = 75, debug: bool = True) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility."""
    merger = ProductMerger(threshold=threshold, debug=debug)
    return merger.merge_products(results)