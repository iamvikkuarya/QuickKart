import time
import sqlite3
import os
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from dotenv import load_dotenv
load_dotenv()

# Set production environment if not set
if not os.environ.get("FLASK_ENV"):
    os.environ["FLASK_ENV"] = "production"

# --- Product scrapers ---
from src.scrapers.blinkit_scraper import run_scraper
from src.scrapers.zepto_scraper import run_zepto_scraper
from src.scrapers.dmart_scraper import run_dmart_scraper

# --- ETA helpers ---
from src.eta.eta_blinkit import get_blinkit_eta
from src.eta.eta_zepto import get_zepto_eta
from src.eta.eta_dmart import get_dmart_eta

from src.scrapers.dmart_location import get_store_details

# --- Merge logic ---
from src.core.utils import merge_products

# --- DB ---
from src.core.db import DB_NAME

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

@app.route("/config")
def get_config():
    return jsonify({
        "maps_api_key": os.getenv("GOOGLE_MAPS_API_KEY")
    })
# --------------------------------------------------------------------------------------
#                               DB SAVE HELPER
# --------------------------------------------------------------------------------------
def save_products(products):
    """Save raw scraper products into SQLite."""
    try:
        from src.core.db import get_db_connection
        conn = get_db_connection()
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
    except Exception as e:
        print(f"⚠️ Save products failed: {e}")

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

    out = {"blinkit": "Service temporarily unavailable", "zepto": "Service temporarily unavailable", "dmart": "Service temporarily unavailable"}
    
    try:
        with ThreadPoolExecutor(max_workers=3) as ex:
            fut_b = ex.submit(get_blinkit_eta, address)
            fut_z = ex.submit(get_zepto_eta, address)
            fut_d = ex.submit(get_dmart_eta, pincode)

            try:
                result = fut_b.result(timeout=25)
                out["blinkit"] = result if result else "N/A"
            except Exception as e:
                print("ETA blinkit error:", e)
                out["blinkit"] = "Service unavailable"
                
            try:
                result = fut_z.result(timeout=25)
                out["zepto"] = result if result else "N/A"
            except Exception as e:
                print("ETA zepto error:", e)
                out["zepto"] = "Service unavailable"
                
            try:
                result = fut_d.result(timeout=25)
                out["dmart"] = result if result else "N/A"
            except Exception as e:
                print("ETA dmart error:", e)
                out["dmart"] = "Service unavailable"
                
    except Exception as e:
        print(f"⚠️ ETA fetch failed: {e}")
        # Return default unavailable message

    eta_cache[eta_key] = (time.time(), out)
    return jsonify(out)

# Individual ETA endpoints for real-time updates
@app.route('/eta/blinkit', methods=['POST'])
def eta_blinkit():
    data = request.get_json() or {}
    address = (data.get('address') or "").strip() or "Azad Nagar, Kothrud, Pune"
    
    try:
        eta = get_blinkit_eta(address)
        return jsonify({"eta": eta or "N/A", "platform": "blinkit"})
    except Exception as e:
        print("ETA blinkit error:", e)
        return jsonify({"eta": "N/A", "platform": "blinkit"})

@app.route('/eta/zepto', methods=['POST'])
def eta_zepto():
    data = request.get_json() or {}
    address = (data.get('address') or "").strip() or "Azad Nagar, Kothrud, Pune"
    
    try:
        eta = get_zepto_eta(address)
        return jsonify({"eta": eta or "N/A", "platform": "zepto"})
    except Exception as e:
        print("ETA zepto error:", e)
        return jsonify({"eta": "N/A", "platform": "zepto"})

@app.route('/eta/dmart', methods=['POST'])
def eta_dmart():
    data = request.get_json() or {}
    pincode = (data.get('pincode') or "").strip() or "411038"
    
    try:
        eta = get_dmart_eta(pincode)
        return jsonify({"eta": eta or "N/A", "platform": "dmart"})
    except Exception as e:
        print("ETA dmart error:", e)
        return jsonify({"eta": "N/A", "platform": "dmart"})

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
@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": time.time()}), 200

@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
