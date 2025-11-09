import re
from rapidfuzz import fuzz
import random

# ------------------------
# Quantity Normalization (IMPROVED)
# ------------------------
def normalize_quantity(qty: str) -> str:
    """Convert all quantity expressions into standard form like '500ml' or '1kg'."""
    if not qty:
        return ""
    
    qty = qty.lower().strip()
    
    # Remove common noise words
    qty = qty.replace('pack', '').replace('pc', '').replace('piece', '').replace('unit', '')
    qty = qty.replace('(', '').replace(')', '').strip()
    
    # Match patterns like "2 x 500 ml" or "2x500ml"
    multi = re.match(r"(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(ml|l|litre|liter|g|gm|gram|kg|kilogram)", qty)
    if multi:
        count, value, unit = multi.groups()
        total = float(count) * float(value)
        
        # Normalize units
        if unit in ['l', 'litre', 'liter']:
            total *= 1000
            unit = "ml"
        elif unit in ['kg', 'kilogram']:
            total *= 1000
            unit = "g"
        elif unit in ['gm', 'gram']:
            unit = "g"
            
        return f"{int(total)}{unit}"
    
    # Match single quantity like "500 ml", "1 L", "400g", "400 gm"
    match = re.search(r"(\d+(?:\.\d+)?)\s*(ml|l|litre|liter|g|gm|gram|kg|kilogram)", qty)
    if match:
        value, unit = match.groups()
        total = float(value)
        
        # Normalize units
        if unit in ['l', 'litre', 'liter']:
            total *= 1000
            unit = "ml"
        elif unit in ['kg', 'kilogram']:
            total *= 1000
            unit = "g"
        elif unit in ['gm', 'gram']:
            unit = "g"
            
        return f"{int(total)}{unit}"
    
    return qty.replace(" ", "")


# ------------------------
# Brand Extraction (IMPROVED)
# ------------------------
def extract_brand(name: str) -> str:
    """Extract brand from product name."""
    if not name:
        return ""
    
    # Common brands to look for
    known_brands = [
        'amul', 'britannia', 'mother dairy', 'nestle', 'parle', 'haldiram',
        'lays', 'kurkure', 'bingo', 'maggi', 'yippee', 'sunfeast', 'oreo',
        'cadbury', 'kitkat', 'dairy milk', 'coca cola', 'pepsi', 'sprite',
        'thums up', 'limca', 'fanta', 'maaza', 'frooti', 'real', 'tropicana',
        'nandini', 'heritage', 'arokya', 'dodla', 'jersey', 'milky mist',
        'id', "sid's farm", 'akshayakalpa'
    ]
    
    name_lower = name.lower()
    
    # Check for known brands first
    for brand in known_brands:
        if brand in name_lower:
            return brand
    
    # Fallback: first word
    return name.strip().split()[0].lower()


# ------------------------
# Clean product name (IMPROVED)
# ------------------------
def clean_name(name: str) -> str:
    """Remove packaging/extra words for fuzzy matching."""
    if not name:
        return ""
    
    name = name.lower()
    
    # More comprehensive noise words
    noise_words = [
        'fresh', 'pouch', 'pack', 'pc', 'piece', 'combo', 'robusta', 'regular',
        'tetra', 'homogenised', 'homogenized', 'standardised', 'standardized',
        'long life', 'farm', 'tub', 'cup', 'stick', 'cone', 'bottle', 'can',
        'jar', 'box', 'unit', 'sachet', 'carton', 'pet', 'fino', 'uht',
        'pasteurized', 'pasteurised', 'organic', 'natural', 'premium'
    ]
    
    for w in noise_words:
        name = name.replace(w, " ")
    
    # Remove special characters but keep hyphens
    name = re.sub(r'[^\w\s-]', ' ', name)
    
    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


# ------------------------
# Quantity closeness (IMPROVED)
# ------------------------
def quantities_close(q1: str, q2: str, tolerance: float = 0.10) -> bool:
    """Check if quantities are within tolerance (default 10%)."""
    num_re = re.compile(r"(\d+)(ml|g)")
    m1, m2 = num_re.match(q1 or ""), num_re.match(q2 or "")
    
    if not (m1 and m2):
        return False
    
    v1, u1 = int(m1.group(1)), m1.group(2)
    v2, u2 = int(m2.group(1)), m2.group(2)
    
    # Must be same unit
    if u1 != u2:
        return False
    
    # Check if within tolerance
    diff = abs(v1 - v2)
    max_val = max(v1, v2)
    
    return diff <= tolerance * max_val


# ------------------------
# Merge logic (IMPROVED)
# ------------------------
def merge_products(results, threshold=75, debug=False):
    """
    Improved merging with better matching logic
    """
    merged = []
    
    for product in results:
        # Skip invalid products
        if not product.get("name") or product["name"].strip().lower() in ("", "n/a"):
            continue
        
        name = product["name"].strip()
        cleaned = clean_name(name)
        brand = extract_brand(name)
        quantity = normalize_quantity(product.get("quantity", ""))
        
        matched_group = None
        best_score = 0
        
        # Try to find matching group
        for group in merged:
            # Skip if platform already exists in this group
            existing_platforms = {p["platform"] for p in group["platforms"]}
            if product["platform"] in existing_platforms:
                continue
            
            group_cleaned = clean_name(group["name"])
            group_brand = extract_brand(group["name"])
            group_qty = normalize_quantity(group["quantity"])
            
            # Calculate similarity score
            name_score = fuzz.token_sort_ratio(cleaned, group_cleaned)
            qty_match = (quantity == group_qty or quantities_close(quantity, group_qty))
            brand_match = (brand == group_brand)
            
            if debug:
                print(f"COMPARE '{cleaned}' vs '{group_cleaned}' → score={name_score}, brand={brand_match}, qty={qty_match}")
            
            # Matching criteria (improved)
            is_match = False
            
            # Strong match: high score + brand + quantity
            if name_score >= threshold and brand_match and qty_match:
                is_match = True
                score = name_score
            
            # Very strong match: very high score + brand (quantity can differ slightly)
            elif name_score >= 90 and brand_match:
                is_match = True
                score = name_score
            
            # Exact brand + quantity match with decent name similarity
            elif name_score >= 70 and brand_match and quantity == group_qty:
                is_match = True
                score = name_score
            
            if is_match and score > best_score:
                matched_group = group
                best_score = score
        
        # Add to matched group or create new
        if matched_group:
            matched_group["platforms"].append({
                "platform": product["platform"],
                "price": product.get("price", "N/A"),
                "delivery_time": product.get("delivery_time"),
                "product_url": product.get("product_url"),
                "image_url": product.get("image_url"),
                "in_stock": product.get("in_stock", True),
            })
        else:
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
    
    # Add price analysis
    for product in merged:
        platforms = product.get("platforms", [])
        
        # Extract numeric prices
        prices = []
        for p in platforms:
            price_str = p.get("price", "0")
            numeric = float(re.sub(r'[^\d.]', '', price_str) or 0)
            prices.append({"platform": p["platform"], "price": numeric})
        
        valid_prices = [p for p in prices if p["price"] > 0]
        
        if len(valid_prices) > 1:
            min_price = min(valid_prices, key=lambda x: x["price"])
            max_price = max(valid_prices, key=lambda x: x["price"])
            
            product["price_analysis"] = {
                "cheapest": min_price["platform"],
                "cheapest_price": min_price["price"],
                "most_expensive": max_price["platform"],
                "most_expensive_price": max_price["price"],
                "savings": max_price["price"] - min_price["price"],
                "savings_percent": round(((max_price["price"] - min_price["price"]) / max_price["price"]) * 100, 1) if max_price["price"] > 0 else 0
            }
    
    # Sort: multi-platform first (by platform count), then shuffle singles
    multi_platform = [m for m in merged if len(m["platforms"]) > 1]
    single_platform = [m for m in merged if len(m["platforms"]) == 1]
    
    # Sort multi-platform by number of platforms (descending)
    multi_platform.sort(key=lambda x: len(x["platforms"]), reverse=True)
    
    # Shuffle single-platform
    random.shuffle(single_platform)
    
    return multi_platform + single_platform
