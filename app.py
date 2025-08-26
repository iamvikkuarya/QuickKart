# app.py
import time
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from blinkit_scraper import run_scraper
from zepto_scraper import run_zepto_scraper
from instamart_scraper import run_instamart_scraper

app = Flask(__name__)

# ✅ Basic in-memory cache: { query_string : (timestamp, result) }
cache = {}

# ⏱️ Cache time-to-live (in seconds)
CACHE_TTL = 300  # 5 minutes

def make_cache_key(query, address, lat, lng):
    # normalize address (lowercase + strip) + coarse lat/lng rounding
    norm_addr = (address or "").strip().lower()
    coarse_lat = round(lat, 3)
    coarse_lng = round(lng, 3)
    return f"{query}_{norm_addr}_{coarse_lat}_{coarse_lng}"

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

    # Use default location if not provided
    latitude = float(lat) if lat else 18.5204
    longitude = float(lng) if lng else 73.8567
    address = address if address else "Kothrud, Pune"

    # 🔍 Create a cache key
    cache_key = make_cache_key(query, address, latitude, longitude)

    # ⚡ Check cache
    if cache_key in cache:
        timestamp, cached_result = cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            print(f"✅ Serving cached result for '{cache_key}'")
            return jsonify(cached_result)
        else:
            print(f"⌛ Cache expired for '{cache_key}', re-scraping...")
            del cache[cache_key]  # Clean up expired entry

    print(f"🔄 Scraping fresh data for '{query}' at {address or (latitude, longitude)}")

    # 🚀 Run scrapers concurrently
    results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        fut_blinkit = ex.submit(run_scraper, query, latitude=latitude, longitude=longitude)
        fut_zepto = ex.submit(run_zepto_scraper, query, address=address or "Pune, Maharashtra")
        fut_instamart = ex.submit(run_instamart_scraper, query, latitude=latitude, longitude=longitude, address=address)

        # Collect results (each guarded so one failure doesn't block others)
        try:
            results += fut_blinkit.result() or []
            print(f"🟢 Blinkit returned {len(results)} total so far")
        except Exception as e:
            print(f"⚠️ Blinkit scraper error: {e}")

        try:
            z = fut_zepto.result() or []
            results += z
            print(f"🟣 Zepto returned {len(z)}")
        except Exception as e:
            print(f"⚠️ Zepto scraper error: {e}")

        try:
            i = fut_instamart.result() or []
            results += i
            print(f"🟠 Instamart returned {len(i)}")
        except Exception as e:
            print(f"⚠️ Instamart scraper error: {e}")

    if not results:
        print("⚠️ No results scraped from either platform")

    # 🗄️ Store in cache
    cache[cache_key] = (time.time(), results)

    return jsonify(results)

@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)  # ⚠️ Don't use debug=True in production
