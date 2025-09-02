import time
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify

# --- Product scrapers ---
from blinkit_scraper import run_scraper
from zepto_scraper import run_zepto_scraper
from dmart_scraper import run_dmart_scraper

# --- ETA helpers ---
from eta_blinkit import get_blinkit_eta
from eta_zepto import get_zepto_eta
from eta_dmart import get_dmart_eta

from dmart_location import get_store_details

# --- Merge logic ---
from utils import merge_products

# --- DB ---
from db import DB_NAME

app = Flask(__name__)

# --------------------------------------------------------------------------------------
#                                   C A C H I N G
# --------------------------------------------------------------------------------------
cache = {}
eta_cache = {}

CACHE_TTL = 300
ETA_CACHE_TTL = 300

def make_cache_key(query, address, pincode):
    norm_addr = (address or "").strip().lower()
    norm_pin = (pincode or "").strip()
    return f"{query}_{norm_addr}_{norm_pin}"

def make_eta_cache_key(address, pincode):
    norm_addr = (address or "").strip().lower()
    norm_pin = (pincode or "").strip()
    return f"eta_{norm_addr}_{norm_pin}"


# --------------------------------------------------------------------------------------
#                               DB SAVE HELPER
# --------------------------------------------------------------------------------------
def save_products(products):
    """Save raw scraper products into SQLite."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for p in products:
        try:
            cur.execute("""
                INSERT INTO products (name, quantity, platform, price, product_url, image_url, in_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                p.get("name"),
                p.get("quantity"),
                p.get("platform"),
                p.get("price"),
                p.get("product_url"),
                p.get("image_url"),
                int(p.get("in_stock", True))
            ))
        except Exception as e:
            print("⚠️ DB insert error:", e, p)
    conn.commit()
    conn.close()

# --------------------------------------------------------------------------------------
#                                 /eta
# --------------------------------------------------------------------------------------
@app.route('/eta', methods=['POST'])
def eta():
    data = request.get_json() or {}
    address = (data.get('address') or "").strip() or "Azad Nagar, Kothrud, Pune"
    pincode = (data.get('pincode') or "").strip() or "411038"

    eta_key = make_eta_cache_key(address, pincode)

    if eta_key in eta_cache:
        ts, result = eta_cache[eta_key]
        if time.time() - ts < ETA_CACHE_TTL:
            return jsonify(result)

    out = {"blinkit": "N/A", "zepto": "N/A", "dmart": "N/A"}
    with ThreadPoolExecutor(max_workers=3) as ex:
        fut_b = ex.submit(get_blinkit_eta, address)
        fut_z = ex.submit(get_zepto_eta, address)
        fut_d = ex.submit(get_dmart_eta, pincode)  # 🔑 use pincode for Dmart

        try:
            out["blinkit"] = fut_b.result(timeout=25) or "N/A"
        except Exception as e:
            print("ETA blinkit error:", e)
        try:
            out["zepto"] = fut_z.result(timeout=25) or "N/A"
        except Exception as e:
            print("ETA zepto error:", e)
        try:
            out["dmart"] = fut_d.result(timeout=25) or "N/A"
        except Exception as e:
            print("ETA dmart error:", e)

    eta_cache[eta_key] = (time.time(), out)
    return jsonify(out)

# --------------------------------------------------------------------------------------
#                                 /search
# --------------------------------------------------------------------------------------
@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = (data.get('query') or "").strip().lower()
    address = (data.get('address') or "").strip()
    pincode = (data.get('pincode') or "").strip() or "411038"

    print(f"📦 Received: query={query}")
    if not query:
        return jsonify({"error": "Missing query"}), 400

    address = address if address else "Kothrud, Pune"

    cache_key = make_cache_key(query, address, pincode)

    if cache_key in cache:
        timestamp, cached_result = cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            print(f"✅ Serving cached result for '{cache_key}'")
            return jsonify(cached_result)
        else:
            print(f"⌛ Cache expired for '{cache_key}', re-scraping...")
            del cache[cache_key]

    print(f"🔄 Scraping fresh data for '{query}' at {address} ({pincode})")

    results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        fut_blinkit = ex.submit(run_scraper, query)
        fut_zepto = ex.submit(run_zepto_scraper, query)
        unique_id, store_id = get_store_details(pincode)
        fut_dmart = ex.submit(run_dmart_scraper, query, store_id) if store_id else None  # 🔑 use pincode for Dmart

        try:
            b = fut_blinkit.result() or []
            results += b
            print(f"🟢 Blinkit returned {len(b)} items")
        except Exception as e:
            print(f"⚠️ Blinkit scraper error: {e}")

        try:
            z = fut_zepto.result() or []
            results += z
            print(f"🟣 Zepto returned {len(z)} items")
        except Exception as e:
            print(f"⚠️ Zepto scraper error: {e}")

        if fut_dmart:
            try:
                d = fut_dmart.result() or []
                results += d
                print(f"🟡 Dmart returned {len(d)} items")
            except Exception as e:
                print(f"⚠️ Dmart scraper error: {e}")

    if not results:
        print("⚠️ No results scraped from any platform")

    # 💾 Save raw results into SQLite
    save_products(results)

    # 🔍 Debug print before merging
    print("\n🔍 DEBUG: Raw scraper output")
    for r in results:
        print(f"   {r['platform']} → {r['name']} | {repr(r['quantity'])}")

    # 🔗 Merge products
    merged_results = merge_products(results)

    # 🔍 Debug print after merging
    print("\n📦 DEBUG: Merged output")
    for m in merged_results:
        print(f"- {m['name']} ({m['quantity']})")
        for p in m['platforms']:
            print(f"   • {p['platform']}: {p['price']} ({p['delivery_time']})")

    cache[cache_key] = (time.time(), merged_results)
    return jsonify(merged_results)

# --------------------------------------------------------------------------------------
@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)
