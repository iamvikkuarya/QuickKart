# app.py
import time
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify

# --- Product scrapers ---
from blinkit_scraper import run_scraper
from zepto_scraper import run_zepto_scraper

# --- ETA helpers ---
from eta_blinkit import get_blinkit_eta
from eta_zepto import get_zepto_eta

# --- NEW: merge logic ---
from utils import merge_products   # 👈 added

app = Flask(__name__)

# --------------------------------------------------------------------------------------
#                                   C A C H I N G
# --------------------------------------------------------------------------------------
cache = {}
eta_cache = {}

CACHE_TTL = 300
ETA_CACHE_TTL = 300

def make_cache_key(query, address, lat, lng):
    norm_addr = (address or "").strip().lower()
    coarse_lat = round(lat, 3)
    coarse_lng = round(lng, 3)
    return f"{query}_{norm_addr}_{coarse_lat}_{coarse_lng}"

def make_eta_cache_key(address, lat, lng):
    norm_addr = (address or "").strip().lower()
    coarse_lat = round(lat, 3)
    coarse_lng = round(lng, 3)
    return f"eta_{norm_addr}_{coarse_lat}_{coarse_lng}"

# --------------------------------------------------------------------------------------
#                                 /eta
# --------------------------------------------------------------------------------------
@app.route('/eta', methods=['POST'])
def eta():
    data = request.get_json() or {}
    lat = data.get('latitude')
    lng = data.get('longitude')
    address = (data.get('address') or "").strip() or "Pune, Maharashtra"

    latitude = float(lat) if lat is not None else 18.5026514
    longitude = float(lng) if lng is not None else 73.807312

    eta_key = make_eta_cache_key(address, latitude, longitude)

    if eta_key in eta_cache:
        ts, result = eta_cache[eta_key]
        if time.time() - ts < ETA_CACHE_TTL:
            return jsonify(result)

    out = {"blinkit": "N/A", "zepto": "N/A", "instamart": "N/A"}
    with ThreadPoolExecutor(max_workers=3) as ex:
        fut_b = ex.submit(get_blinkit_eta, latitude, longitude)
        fut_z = ex.submit(get_zepto_eta, address)

        try:
            out["blinkit"] = fut_b.result(timeout=25) or "N/A"
        except Exception as e:
            print("ETA blinkit error:", e)
        try:
            out["zepto"] = fut_z.result(timeout=25) or "N/A"
        except Exception as e:
            print("ETA zepto error:", e)

    eta_cache[eta_key] = (time.time(), out)
    return jsonify(out)

# --------------------------------------------------------------------------------------
#                                 /search
# --------------------------------------------------------------------------------------
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

    latitude = float(lat) if lat else 18.5026501
    longitude = float(lng) if lng else 73.8073136
    address = address if address else "Kothrud, Pune"

    cache_key = make_cache_key(query, address, latitude, longitude)

    if cache_key in cache:
        timestamp, cached_result = cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            print(f"✅ Serving cached result for '{cache_key}'")
            return jsonify(cached_result)
        else:
            print(f"⌛ Cache expired for '{cache_key}', re-scraping...")
            del cache[cache_key]

    print(f"🔄 Scraping fresh data for '{query}' at {address or (latitude, longitude)}")

    results = []
    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_blinkit = ex.submit(run_scraper, query)
        fut_zepto = ex.submit(run_zepto_scraper, query)

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

    if not results:
        print("⚠️ No results scraped from either platform")

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
