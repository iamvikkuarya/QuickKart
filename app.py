import time
import sqlite3
import os
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from dotenv import load_dotenv
load_dotenv()

# --- Product scrapers ---
from src.scrapers.blinkit_scraper import run_scraper
from src.scrapers.zepto_scraper import run_zepto_scraper
from src.scrapers.dmart_scraper import run_dmart_scraper
from src.scrapers.instamart_scraper import run_instamart_scraper

# --- ETA helpers ---
from src.eta.eta_blinkit import get_blinkit_eta
from src.eta.eta_zepto import get_zepto_eta
from src.eta.eta_dmart import get_dmart_eta
from src.eta.eta_instamart import get_instamart_eta

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
        except Exception:
            pass  # Silently skip DB errors
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

    out = {"blinkit": "N/A", "zepto": "N/A", "dmart": "N/A", "instamart": "N/A"}
    with ThreadPoolExecutor(max_workers=4) as ex:
        fut_b = ex.submit(get_blinkit_eta, address)
        fut_z = ex.submit(get_zepto_eta, address)
        fut_d = ex.submit(get_dmart_eta, pincode)
        fut_i = ex.submit(get_instamart_eta, address)  # 🔑 use pincode for Dmart

        try:
            out["blinkit"] = fut_b.result(timeout=25) or "N/A"
        except Exception:
            pass
        try:
            out["zepto"] = fut_z.result(timeout=25) or "N/A"
        except Exception:
            pass
        try:
            out["dmart"] = fut_d.result(timeout=25) or "N/A"
        except Exception:
            pass
        try:
            out["instamart"] = fut_i.result(timeout=20) or "N/A"
        except Exception:
            pass

    eta_cache[eta_key] = (time.time(), out)
    return jsonify(out)

# Individual ETA endpoints for real-time updates
@app.route('/eta/blinkit', methods=['POST'])
def eta_blinkit():
    data = request.get_json() or {}
    address = (data.get('address') or "").strip() or "Azad Nagar, Kothrud, Pune"
    pincode = (data.get('pincode') or "").strip() or "411038"
    
    # Check cache first
    eta_key = make_eta_cache_key(address, pincode)
    if eta_key in eta_cache:
        ts, cached_result = eta_cache[eta_key]
        if time.time() - ts < ETA_CACHE_TTL:
            return jsonify({"eta": cached_result.get("blinkit", "N/A"), "platform": "blinkit"})
    
    try:
        eta = get_blinkit_eta(address)
        result = {"eta": eta or "N/A", "platform": "blinkit"}
        
        # Update cache with this result
        if eta_key in eta_cache:
            ts, cached_data = eta_cache[eta_key]
            cached_data["blinkit"] = eta or "N/A"
            eta_cache[eta_key] = (time.time(), cached_data)
        else:
            eta_cache[eta_key] = (time.time(), {"blinkit": eta or "N/A", "zepto": "N/A", "dmart": "N/A"})
        
        return jsonify(result)
    except Exception:
        return jsonify({"eta": "N/A", "platform": "blinkit"})

@app.route('/eta/zepto', methods=['POST'])
def eta_zepto():
    data = request.get_json() or {}
    address = (data.get('address') or "").strip() or "Azad Nagar, Kothrud, Pune"
    pincode = (data.get('pincode') or "").strip() or "411038"
    
    # Check cache first
    eta_key = make_eta_cache_key(address, pincode)
    if eta_key in eta_cache:
        ts, cached_result = eta_cache[eta_key]
        if time.time() - ts < ETA_CACHE_TTL:
            return jsonify({"eta": cached_result.get("zepto", "N/A"), "platform": "zepto"})
    
    try:
        eta = get_zepto_eta(address)
        result = {"eta": eta or "N/A", "platform": "zepto"}
        
        # Update cache with this result
        if eta_key in eta_cache:
            ts, cached_data = eta_cache[eta_key]
            cached_data["zepto"] = eta or "N/A"
            eta_cache[eta_key] = (time.time(), cached_data)
        else:
            eta_cache[eta_key] = (time.time(), {"blinkit": "N/A", "zepto": eta or "N/A", "dmart": "N/A"})
        
        return jsonify(result)
    except Exception:
        return jsonify({"eta": "N/A", "platform": "zepto"})

@app.route('/eta/dmart', methods=['POST'])
def eta_dmart():
    data = request.get_json() or {}
    address = (data.get('address') or "").strip() or "Azad Nagar, Kothrud, Pune"
    pincode = (data.get('pincode') or "").strip() or "411038"
    
    # Check cache first
    eta_key = make_eta_cache_key(address, pincode)
    if eta_key in eta_cache:
        ts, cached_result = eta_cache[eta_key]
        if time.time() - ts < ETA_CACHE_TTL:
            return jsonify({"eta": cached_result.get("dmart", "N/A"), "platform": "dmart"})
    
    try:
        eta = get_dmart_eta(pincode)
        result = {"eta": eta or "N/A", "platform": "dmart"}
        
        # Update cache with this result
        if eta_key in eta_cache:
            ts, cached_data = eta_cache[eta_key]
            cached_data["dmart"] = eta or "N/A"
            eta_cache[eta_key] = (time.time(), cached_data)
        else:
            eta_cache[eta_key] = (time.time(), {"blinkit": "N/A", "zepto": "N/A", "dmart": eta or "N/A"})
        
        return jsonify(result)
    except Exception:
        return jsonify({"eta": "N/A", "platform": "dmart"})

@app.route('/eta/instamart', methods=['POST'])
def eta_instamart():
    data = request.get_json() or {}
    address = (data.get('address') or "").strip() or "Azad Nagar, Kothrud, Pune"
    pincode = (data.get('pincode') or "").strip() or "411038"
    
    # Check cache first
    eta_key = make_eta_cache_key(address, pincode)
    if eta_key in eta_cache:
        ts, cached_result = eta_cache[eta_key]
        if time.time() - ts < ETA_CACHE_TTL:
            return jsonify({"eta": cached_result.get("instamart", "N/A"), "platform": "instamart"})
    
    try:
        eta = get_instamart_eta(address)
        result = {"eta": eta or "N/A", "platform": "instamart"}
        
        # Update cache with this result
        if eta_key in eta_cache:
            ts, cached_data = eta_cache[eta_key]
            cached_data["instamart"] = eta or "N/A"
            eta_cache[eta_key] = (time.time(), cached_data)
        else:
            eta_cache[eta_key] = (time.time(), {"blinkit": "N/A", "zepto": "N/A", "dmart": "N/A", "instamart": eta or "N/A"})
        
        return jsonify(result)
    except Exception:
        return jsonify({"eta": "N/A", "platform": "instamart"})

# --------------------------------------------------------------------------------------
#                                 /search
# --------------------------------------------------------------------------------------
@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = (data.get('query') or "").strip().lower()
    address = (data.get('address') or "").strip()
    pincode = (data.get('pincode') or "").strip() or "411038"

    if not query:
        return jsonify({"error": "Missing query"}), 400

    address = address if address else "Kothrud, Pune"

    cache_key = make_cache_key(query, address, pincode)

    if cache_key in cache:
        timestamp, cached_result = cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return jsonify(cached_result)
        else:
            del cache[cache_key]

    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        fut_blinkit = ex.submit(run_scraper, query)
        fut_zepto = ex.submit(run_zepto_scraper, query)
        unique_id, store_id = get_store_details(pincode)
        fut_dmart = ex.submit(run_dmart_scraper, query, store_id) if store_id else None
        fut_instamart = ex.submit(run_instamart_scraper, query, address)  # 🔑 use pincode for Dmart

        try:
            b = fut_blinkit.result() or []
            results += b
        except Exception:
            pass

        try:
            z = fut_zepto.result() or []
            results += z
        except Exception:
            pass

        if fut_dmart:
            try:
                d = fut_dmart.result() or []
                results += d
            except Exception:
                pass
        
        try:
            i = fut_instamart.result(timeout=20) or []
            results += i
        except Exception:
            pass

    # Save raw results into SQLite
    save_products(results)

    # Merge products
    merged_results = merge_products(results)

    cache[cache_key] = (time.time(), merged_results)
    return jsonify(merged_results)

# --------------------------------------------------------------------------------------
@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)
