import re
from rapidfuzz import fuzz
import random

# ------------------------
# Quantity Normalization
# ------------------------
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


# ------------------------
# Brand Extraction
# ------------------------
def extract_brand(name: str) -> str:
    """Extract brand (first word heuristic)."""
    if not name:
        return ""
    return name.strip().split()[0].lower()


# ------------------------
# Clean product name
# ------------------------
def clean_name(name: str) -> str:
    """Remove packaging/extra words for fuzzy matching."""
    if not name:
        return ""
    name = name.lower()

    noise_words = [
        "fresh", "pouch", "pack", "pc", "combo", "robusta", "regular",
        "tetra", "homogenised", "homogenized", "standardised", "standardized",
        "long life", "farm", "tub", "cup", "stick", "cone", "bottle", "can",
        "jar", "box", "unit", "sachet", "carton"
    ]
    for w in noise_words:
        name = name.replace(w, "")

    return re.sub(r"\s+", " ", name).strip()


# ------------------------
# Helper: quantity closeness
# ------------------------
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


# ------------------------
# Merge logic
# ------------------------
def merge_products(results, threshold=75, debug=True):
    merged = []

    for product in results:
        if not product.get("name") or product["name"].strip().lower() in ("", "n/a"):
            continue

        name = product["name"].strip()
        cleaned = clean_name(name)
        brand = extract_brand(name)
        quantity = normalize_quantity(product.get("quantity", ""))

        matched_group = None

        for group in merged:
            existing_platforms = {p["platform"] for p in group["platforms"]}
            if product["platform"] in existing_platforms:
                continue

            group_cleaned = clean_name(group["name"])
            group_brand = extract_brand(group["name"])
            group_qty = normalize_quantity(group["quantity"])

            score = fuzz.token_sort_ratio(cleaned, group_cleaned)
            qty_match = (quantity == group_qty or quantities_close(quantity, group_qty))
            brand_match = (brand == group_brand)

            if debug:
                print(
                    f"COMPARE '{cleaned}' vs '{group_cleaned}' "
                    f"→ score={score}, qty={quantity} vs {group_qty}, "
                    f"qty_match={qty_match}, brand_match={brand_match}"
                )

            if ((score >= threshold and qty_match and brand_match) or
                (score >= 90 and brand_match)):
                matched_group = group
                break

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

    # ✅ Split merged vs unmerged
    multi_platform = [m for m in merged if len(m["platforms"]) > 1]
    single_platform = [m for m in merged if len(m["platforms"]) == 1]

    # 🔀 Shuffle single-platform listings
    random.shuffle(single_platform)

    # ✅ Return merged first, shuffled singles after
    return multi_platform + single_platform