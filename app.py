import time
import sqlite3
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from cachetools import TTLCache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

# --- Logging setup ---
from src.core.logging_config import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

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
from src.core.db import DB_NAME, init_db

# Initialize database on startup
init_db()
logger.info("Database initialized")

app = Flask(__name__)

# --- Rate Limiting ---
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://"
)
logger.info("Rate limiting enabled")

# --------------------------------------------------------------------------------------
#                                   C A C H I N G
# --------------------------------------------------------------------------------------
# Using TTLCache with max size to prevent memory leaks
CACHE_TTL = 300
ETA_CACHE_TTL = 300
MAX_CACHE_SIZE = 500

cache = TTLCache(maxsize=MAX_CACHE_SIZE, ttl=CACHE_TTL)
eta_cache = TTLCache(maxsize=MAX_CACHE_SIZE, ttl=ETA_CACHE_TTL)

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

    # TTLCache handles expiration automatically
    if eta_key in eta_cache:
        logger.debug(f"ETA cache hit for {eta_key}")
        return jsonify(eta_cache[eta_key])

    out = {"blinkit": "N/A", "zepto": "N/A", "dmart": "N/A", "instamart": "N/A"}
    with ThreadPoolExecutor(max_workers=4) as ex:
        fut_b = ex.submit(get_blinkit_eta, address)
        fut_z = ex.submit(get_zepto_eta, address)
        fut_d = ex.submit(get_dmart_eta, pincode)
        fut_i = ex.submit(get_instamart_eta, address)

        try:
            out["blinkit"] = fut_b.result(timeout=25) or "N/A"
        except Exception as e:
            logger.warning(f"Blinkit ETA timeout: {e}")
        try:
            out["zepto"] = fut_z.result(timeout=25) or "N/A"
        except Exception as e:
            logger.warning(f"Zepto ETA timeout: {e}")
        try:
            out["dmart"] = fut_d.result(timeout=25) or "N/A"
        except Exception as e:
            logger.warning(f"DMart ETA timeout: {e}")
        try:
            out["instamart"] = fut_i.result(timeout=20) or "N/A"
        except Exception as e:
            logger.warning(f"Instamart ETA timeout: {e}")

    eta_cache[eta_key] = out
    return jsonify(out)

# Individual ETA endpoint - refactored to reduce duplication
ETA_HANDLERS = {
    'blinkit': lambda addr, pin: get_blinkit_eta(addr),
    'zepto': lambda addr, pin: get_zepto_eta(addr),
    'dmart': lambda addr, pin: get_dmart_eta(pin),
    'instamart': lambda addr, pin: get_instamart_eta(addr),
}

@app.route('/eta/<platform>', methods=['POST'])
def eta_single(platform):
    """Single endpoint for individual platform ETAs"""
    if platform not in ETA_HANDLERS:
        return jsonify({"error": f"Unknown platform: {platform}"}), 400
    
    data = request.get_json() or {}
    address = (data.get('address') or "").strip() or "Azad Nagar, Kothrud, Pune"
    pincode = (data.get('pincode') or "").strip() or "411038"
    
    eta_key = make_eta_cache_key(address, pincode)
    
    # Check cache first (TTLCache handles expiration)
    if eta_key in eta_cache:
        cached = eta_cache[eta_key]
        if platform in cached:
            return jsonify({"eta": cached.get(platform, "N/A"), "platform": platform})
    
    try:
        eta_result = ETA_HANDLERS[platform](address, pincode)
        result = {"eta": eta_result or "N/A", "platform": platform}
        
        # Update cache
        if eta_key in eta_cache:
            eta_cache[eta_key][platform] = eta_result or "N/A"
        else:
            eta_cache[eta_key] = {platform: eta_result or "N/A"}
        
        return jsonify(result)
    except Exception as e:
        logger.warning(f"{platform} ETA error: {e}")
        return jsonify({"eta": "N/A", "platform": platform})

# --------------------------------------------------------------------------------------
#                                 /search
# --------------------------------------------------------------------------------------
@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = (data.get('query') or "").strip().lower()
    address = (data.get('address') or "").strip()
    pincode = (data.get('pincode') or "").strip() or "411038"

    platform_filter = (data.get('platform') or "").strip().lower()

    if not query:
        return jsonify({"error": "Missing query"}), 400

    address = address if address else "Kothrud, Pune"
    # Update cache key to include platform filter so specific searches are cached separately
    cache_key = f"{make_cache_key(query, address, pincode)}_{platform_filter}"

    # TTLCache handles expiration automatically
    if cache_key in cache:
        logger.debug(f"Search cache hit for '{query}' (platform: {platform_filter})")
        return jsonify(cache[cache_key])

    logger.info(f"Searching for '{query}' at {address} (platform: {platform_filter or 'all'})")
    results = []
    
    with ThreadPoolExecutor(max_workers=4) as ex:
        # Only submit tasks if no filter is set OR if the specific platform is requested
        fut_blinkit = ex.submit(run_scraper, query) if (not platform_filter or platform_filter == 'blinkit') else None
        fut_zepto = ex.submit(run_zepto_scraper, query) if (not platform_filter or platform_filter == 'zepto') else None
        
        unique_id, store_id = get_store_details(pincode)
        should_run_dmart = (store_id and (not platform_filter or platform_filter == 'dmart'))
        fut_dmart = ex.submit(run_dmart_scraper, query, store_id) if should_run_dmart else None
        
        fut_instamart = ex.submit(run_instamart_scraper, query, address) if (not platform_filter or platform_filter == 'instamart') else None

        if fut_blinkit:
            try:
                b = fut_blinkit.result(timeout=30) or []
                results += b
                logger.debug(f"Blinkit: {len(b)} products")
            except Exception as e:
                logger.warning(f"Blinkit scraper failed: {e}")

        if fut_zepto:
            try:
                z = fut_zepto.result(timeout=30) or []
                results += z
                logger.debug(f"Zepto: {len(z)} products")
            except Exception as e:
                logger.warning(f"Zepto scraper failed: {e}")

        if fut_dmart:
            try:
                d = fut_dmart.result(timeout=30) or []
                results += d
                logger.debug(f"DMart: {len(d)} products")
            except Exception as e:
                logger.warning(f"DMart scraper failed: {e}")
        
        if fut_instamart:
            try:
                i = fut_instamart.result(timeout=30) or []
                results += i
                logger.debug(f"Instamart: {len(i)} products")
            except Exception as e:
                logger.warning(f"Instamart scraper failed: {e}")

    # Save raw results into SQLite
    save_products(results)
    logger.info(f"Found {len(results)} total products for '{query}'")

    # Merge products
    merged_results = merge_products(results)

    cache[cache_key] = merged_results
    return jsonify(merged_results)

# --------------------------------------------------------------------------------------
@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
