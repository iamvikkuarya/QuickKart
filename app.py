# app.py
import time
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify

# --- Product scrapers (existing) ---
from blinkit_scraper import run_scraper                # Blinkit product search
from zepto_scraper import run_zepto_scraper            # Zepto product search

# --- NEW: tiny ETA helpers (we'll add these in each scraper file next) ---
# These functions should do just one thing: open the site with the user's location and read the delivery time (ETA).
from eta_blinkit import get_blinkit_eta            # -> returns a string like "15 mins" or "N/A"
from eta_zepto import get_zepto_eta                # -> returns a string like "12 mins" or "N/A"

app = Flask(__name__)

# --------------------------------------------------------------------------------------
#                                   C A C H I N G
# --------------------------------------------------------------------------------------
# We keep two simple in-memory caches:
# 1) `cache` for product search results (keyed by query+coarse location) — short TTL to avoid stale prices.
# 2) `eta_cache` for per-location ETAs (keyed by coarse location) — short TTL since ETAs fluctuate.

# ✅ Basic in-memory cache for SEARCH: { cache_key : (timestamp, results_list) }
cache = {}

# ✅ Basic in-memory cache for ETAs:   { eta_cache_key : (timestamp, {"blinkit": "...","zepto": "...","instamart": "..."}) }
eta_cache = {}

# ⏱️ Cache time-to-live (in seconds)
CACHE_TTL = 300      # 5 minutes for search results
ETA_CACHE_TTL = 300  # 5 minutes for ETAs

def make_cache_key(query, address, lat, lng):
    """
    Build a stable cache key for product searches:
    - Normalize address (lowercase, stripped)
    - Round lat/lng to 3 decimals (≈100m) to avoid cache miss on tiny GPS jitter
    - Include the query string
    """
    norm_addr = (address or "").strip().lower()
    coarse_lat = round(lat, 3)
    coarse_lng = round(lng, 3)
    return f"{query}_{norm_addr}_{coarse_lat}_{coarse_lng}"

def make_eta_cache_key(address, lat, lng):
    """
    Build a stable cache key for ETAs:
    - Same coarse rounding, but no query (ETAs are independent of the search term)
    """
    norm_addr = (address or "").strip().lower()
    coarse_lat = round(lat, 3)
    coarse_lng = round(lng, 3)
    return f"eta_{norm_addr}_{coarse_lat}_{coarse_lng}"

# --------------------------------------------------------------------------------------
#                                 N E W   /eta   A P I
# --------------------------------------------------------------------------------------
# Purpose:
# - As soon as the user lands (and we have geolocation), the frontend will POST here.
# - We spin up 3 tiny Playwright jobs in parallel (one per platform) that ONLY read the delivery time.
# - We cache the result for a short time so subsequent page loads don't re-open browsers immediately.
# - Response shape: {"blinkit": "15 mins", "zepto": "12 mins", "instamart": "18 mins"}
@app.route('/eta', methods=['POST'])
def eta():
    data = request.get_json() or {}
    lat = data.get('latitude')
    lng = data.get('longitude')
    address = (data.get('address') or "").strip() or "Pune, Maharashtra"

    # Use defaults if frontend didn't pass coords (keeps endpoint robust)
    latitude = float(lat) if lat is not None else 18.5026514
    longitude = float(lng) if lng is not None else 73.807312

    # 🔑 Build a per-location cache key
    eta_key = make_eta_cache_key(address, latitude, longitude)

    # ⚡ Serve from cache if fresh
    if eta_key in eta_cache:
        ts, result = eta_cache[eta_key]
        if time.time() - ts < ETA_CACHE_TTL:
            return jsonify(result)

    # 🚀 Run all three ETA lookups concurrently (fast + independent)
    out = {"blinkit": "N/A", "zepto": "N/A", "instamart": "N/A"}
    with ThreadPoolExecutor(max_workers=3) as ex:
        fut_b = ex.submit(get_blinkit_eta, latitude, longitude)       # Blinkit uses lat/lng
        fut_z = ex.submit(get_zepto_eta, address)                      # Zepto prefers an address string

        # We keep try/except per-platform so one failure doesn't break the whole response
        try:
            out["blinkit"] = fut_b.result(timeout=25) or "N/A"
        except Exception as e:
            print("ETA blinkit error:", e)
        try:
            out["zepto"] = fut_z.result(timeout=25) or "N/A"
        except Exception as e:
            print("ETA zepto error:", e)

    # 🗄️ Cache ETAs for this coarse location
    eta_cache[eta_key] = (time.time(), out)

    return jsonify(out)

# --------------------------------------------------------------------------------------
#                               /search  (existing, concurrent)
# --------------------------------------------------------------------------------------
# Purpose:
# - Handles the product search query. We run the 3 scrapers in parallel and merge results.
# - The ETAs shown in the UI will come from /eta (fetched earlier by the frontend),
#   but you can also choose to attach the current ETAs here if desired (not required).
@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = (data.get('query') or "").strip().lower()
    lat = data.get('latitude')
    lng = data.get('longitude')
    address = (data.get('address') or "").strip()

    print(f"📦 Received: query={query}, lat={lat}, lng={lng}")
    if not query:
        return jsonify({"error": "Missing query"}), 400

    # 🌍 Default location fallback keeps things working even if geolocation is blocked
    latitude = float(lat) if lat else 18.5026501
    longitude = float(lng) if lng else 73.8073136
    address = address if address else "Kothrud, Pune"

    # 🔑 Build a cache key that reflects both query and coarse location
    cache_key = make_cache_key(query, address, latitude, longitude)

    # ⚡ Serve from cache if fresh (prevents hammering scrapers for repeat queries)
    if cache_key in cache:
        timestamp, cached_result = cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            print(f"✅ Serving cached result for '{cache_key}'")
            return jsonify(cached_result)
        else:
            print(f"⌛ Cache expired for '{cache_key}', re-scraping...")
            del cache[cache_key]  # Clean up expired entry

    print(f"🔄 Scraping fresh data for '{query}' at {address or (latitude, longitude)}")

    # 🚀 Run scrapers concurrently (1 per platform)
    results = []
    with ThreadPoolExecutor(max_workers=2) as ex:
        # Submit one job per platform
        fut_blinkit = ex.submit(run_scraper, query)
        fut_zepto = ex.submit(run_zepto_scraper, query)

        # Collect results (each guarded so one failure doesn't block others)
    try:
        b = fut_blinkit.result() or []
        results += b
        print(f"🟢 Blinkit returned {len(b)}")
    except Exception as e:
        print(f"⚠️ Blinkit scraper error: {e}")

    try:
        z = fut_zepto.result() or []
        results += z
        print(f"🟣 Zepto returned {len(z)}")
    except Exception as e:
        print(f"⚠️ Zepto scraper error: {e}")

    if not results:
        print("⚠️ No results scraped from either platform")

    # 🗄️ Store in cache and return
    cache[cache_key] = (time.time(), results)
    return jsonify(results)

# --------------------------------------------------------------------------------------
#                                 S T A T I C   H O M E
# --------------------------------------------------------------------------------------
@app.route('/')
def home():
    # Serves /static/index.html (via Flask static handler)
    return app.send_static_file('index.html')

# --------------------------------------------------------------------------------------
#                             D E V   S E R V E R   N O T E
# --------------------------------------------------------------------------------------
# In production, run behind gunicorn/uwsgi and disable debug. Debug True can spawn a
# reloader process which may double-invoke code. Keep it here for dev convenience.
if __name__ == '__main__':
    app.run(debug=True)  # ⚠️ Don't use debug=True in production
