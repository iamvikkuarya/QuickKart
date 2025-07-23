# app.py
import sqlite3
import json
import time
from flask import Flask, request, jsonify
from blinkit_scraper import run_scraper, product_key, is_complete

app = Flask(__name__)
DB_PATH = 'product.db'

def create_table_if_not_exists():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            platform TEXT NOT NULL,
            data TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_table_if_not_exists()

def get_related_results(query, platform, min_results=10, expiry_seconds=600):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        '''SELECT data, timestamp FROM products 
           WHERE platform = ? 
           ORDER BY timestamp DESC''',
        (platform,)
    )
    all_data = []
    seen_urls = set()
    now = int(time.time())

    for row in c.fetchall():
        data, timestamp = row
        if now - timestamp > expiry_seconds:
            continue
        parsed = json.loads(data)
        filtered = [
            item for item in parsed
            if query.lower() in item.get("name", "").lower()
            and product_key(item) not in seen_urls
        ]
        for item in filtered:
            seen_urls.add(product_key(item))
        all_data.extend(filtered)
        if len(all_data) >= min_results:
            break
    conn.close()
    return all_data if len(all_data) >= min_results else None

def save_to_db(query, platform, result):
    unique = {}
    for item in result:
        key = product_key(item)
        if key and is_complete(item):
            unique[key] = item
    if not unique:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'INSERT INTO products (query, platform, data, timestamp) VALUES (?, ?, ?, ?)',
        (query, platform, json.dumps(list(unique.values())), int(time.time()))
    )
    conn.commit()
    conn.close()

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query', '').strip().lower()
    lat = data.get('latitude')
    lng = data.get('longitude')

    print(f"📦 Received: query={query}, lat={lat}, lng={lng}")
    if not query:
        return jsonify({"error": "Missing query"}), 400

    cached_results = get_related_results(query=query, platform="blinkit", min_results=10)
    if cached_results:
        print(f"✅ Served cached results for '{query}'")
        return jsonify(cached_results)

    print(f"🔄 Scraping for fresh results of '{query}' at ({lat}, {lng})")
    result = run_scraper(query, latitude=lat, longitude=lng)
    if result:
        save_to_db(query=query, platform="blinkit", result=result)
    return jsonify(result)

@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)
