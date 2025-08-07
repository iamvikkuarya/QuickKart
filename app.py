# app.py
import json
import time
from flask import Flask, request, jsonify
from blinkit_scraper import run_scraper

app = Flask(__name__)

# ✅ Basic in-memory cache: { query_string : (timestamp, result) }
cache = {}

# ⏱️ Cache time-to-live (in seconds)
CACHE_TTL = 300  # 5 minutes

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query', '').strip().lower()
    lat = data.get('latitude')
    lng = data.get('longitude')
    address = data.get('address', '').strip()

    print(f"📦 Received: query={query}, lat={lat}, lng={lng}")
    if not query:
        return jsonify({"error": "Missing query"}), 400

    # Use default location if not provided
    latitude = float(lat) if lat else 18.5204
    longitude = float(lng) if lng else 73.8567
    address = address if address else "Kothrud, Pune"

    # 🔍 Create a cache key using query and location
    cache_key = f"{query}_{address or latitude}_{longitude}"

    # ⚡ Check cache for existing result
    if cache_key in cache:
        timestamp, cached_result = cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            print(f"✅ Serving cached result for '{cache_key}'")
            return jsonify(cached_result)
        else:
            print(f"⌛ Cache expired for '{cache_key}', re-scraping...")
            del cache[cache_key]  # Clean up expired entry

    print(f"🔄 Scraping fresh data for '{query}' at {address or (latitude, longitude)}")

    # 🚀 Run scraper and store result in cache
    blinkit_results = run_scraper(query, latitude=latitude, longitude=longitude)
    #zepto_results = run_zepto_scraper(query, address=address)

    result = blinkit_results #+ zepto_results
    cache[cache_key] = (time.time(), result)

    return jsonify(result)

@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)
