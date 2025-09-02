# dmart_scraper.py
import requests
from dmart_location import BASE_HEADERS

def run_dmart_scraper(query: str, store_id: str):
    """
    Scrape products from Dmart for a specific query and store.
    Store ID ensures results are location-specific.
    """
    url = f"https://digital.dmart.in/api/v3/search/{query}?page=1&size=100&channel=web&storeId={store_id}"
    resp = requests.get(url, headers=BASE_HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    raw_products = data.get("products", [])
    print(f"🔎 totalRecords={data.get('totalRecords')}, products in JSON={len(raw_products)}")

    products = []
    for product in raw_products:
        for sku in product.get("sKUs", []):
            try:
                name = sku.get("name", "").strip()
                price = sku.get("priceSALE")  # SALE price only
                qty = sku.get("variantTextValue", "")
                img_key = sku.get("productImageKey", "")

                # Dmart image convention
                image_url = f"https://cdn.dmart.in/images/products/{img_key}_5_P.jpg" if img_key else ""

                # Correct product URL format
                seo_token = product.get("seo_token_ntk", "")
                sku_id = sku.get("skuUniqueID")
                product_url = f"https://www.dmart.in/product/{seo_token}?selectedProd={sku_id}" if seo_token and sku_id else ""

                products.append({
                    "platform": "dmart",
                    "name": name,
                    "price": f"₹{price}" if price else "N/A",
                    "quantity": qty,
                    "image_url": image_url,
                    "product_url": product_url,
                    "delivery_time": "N/A",  # ETA handled separately
                    "in_stock": sku.get("buyable") == "true"
                })
            except Exception as e:
                print("⚠️ Error parsing SKU:", e)
                continue

    print(f"✅ Parsed {len(products)} products")
    return products


if __name__ == "__main__":
    # Example: test with storeId
    test_store_id = "10680"  # Replace with real storeId
    results = run_dmart_scraper("milk", test_store_id)
    print("✅ Sample product:", results[0] if results else "No results")
