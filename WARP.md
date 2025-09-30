# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project: QuickKart — Grocery price comparison across multiple platforms (Blinkit, Zepto, DMart; Instamart prototype)

Commands (PowerShell on Windows)

- Python environment
  - python -m venv .venv
  - .\.venv\Scripts\Activate.ps1
  - pip install -r requirements.txt
  - pip install playwright
  - playwright install
  - Note: Code uses additional libraries not listed in requirements.txt: bs4 (BeautifulSoup) and rapidfuzz. If you see ModuleNotFoundError, install them:
    - pip install beautifulsoup4 rapidfuzz

- Initialize local SQLite DB (creates product.db)
  - python db.py

- Run the Flask app (development)
  - $env:FLASK_APP = "app.py"
  - flask run --reload
  - Or: python app.py

- Tests (pytest)
  - Run all tests: pytest -q
  - Run a single test file: pytest tests\test_something.py -q
  - Run a single test by node id: pytest tests\test_something.py::TestClass::test_case -q
  - Run by keyword: pytest -k "keyword" -q

- Playwright headful debug (optional, helpful for scraper selector work)
  - Set headless=False in the relevant scraper and run the module directly, e.g.:
    - python blinkit_scraper.py
    - python zepto_scraper.py

- Lint/format
  - No linter/formatter is configured in this repo.

High-level architecture and flow

- Flask app (app.py)
  - Endpoints
    - GET / → serves static/index.html if present.
    - GET /config → returns { maps_api_key } from environment (.env via python-dotenv).
    - POST /search → body { query, address?, pincode? }. In parallel, runs scrapers for Blinkit and Zepto; resolves DMart storeId from pincode and, if available, scrapes DMart. Saves raw results to SQLite, merges comparable products, caches the merged response, and returns it.
    - POST /eta → body { address, pincode }. In parallel, fetches delivery ETA for Blinkit, Zepto, and DMart; caches and returns the result.
  - Caching
    - In-memory dicts for search and ETA with TTLs (CACHE_TTL, ETA_CACHE_TTL; default 300s). Cache keys include query/address/pincode as applicable.
  - Concurrency
    - ThreadPoolExecutor is used to run scrapers and ETA fetchers in parallel to reduce overall latency.

- Scrapers
  - blinkit_scraper.py (run_scraper)
    - Playwright (Chromium) + BeautifulSoup to parse the rendered product grid from the global search URL. Produces normalized dicts with keys: platform, name, price, quantity, image_url, product_url, in_stock.
  - zepto_scraper.py (run_zepto_scraper)
    - Playwright (Chromium). Queries global search and extracts product cards via DOM selectors.
  - dmart_scraper.py (run_dmart_scraper)
    - Pure HTTP (requests) against DMart JSON APIs using a resolved storeId (location-specific). Normalizes SKUs into the common schema.
  - instamart_scraper.py (run_instamart_mobile_scraper)
    - Prototype mobile-flow scraper using Playwright with mobile UA and geolocation. Not wired into /search.

- ETA helpers
  - eta_blinkit.py (get_blinkit_eta)
  - eta_zepto.py (get_zepto_eta)
  - eta_dmart.py (get_dmart_eta)
    - DMart ETA is derived via JSON APIs; requires a pincode/address to resolve a uniqueId and storeId.
  - eta_instamart.py (get_instamart_eta)
    - Prototype, not used by app.py.

- Location → store resolution for DMart
  - dmart_location.py (get_store_details)
    - Resolves pincode → (uniqueId, storeId) through DMart APIs; storeId then enables product search for the correct fulfillment location.

- Product merge logic
  - utils.py (merge_products)
    - Fuzzy grouping across platforms using rapidfuzz.token_sort_ratio on cleaned names, plus brand and normalized quantity comparison. Outputs a list of merged items where each item has a platforms[] array of per-platform offers. Single‑platform items are shuffled; multi‑platform groups are listed first.

- Persistence
  - SQLite database (product.db), managed in db.py
    - Table products stores raw per-platform results from each search with a scraped_at timestamp. app.py calls save_products() after scraping.

Configuration

- Environment
  - .env is loaded via python-dotenv. Expected keys:
    - GOOGLE_MAPS_API_KEY: for the browser frontend to request map features via /config.
    - FLASK_ENV=development for local dev.

- Dependencies
  - requirements.txt: Flask, python-dotenv, playwright, requests, pytest.
  - Code additionally imports: beautifulsoup4 (bs4), rapidfuzz.
  - Playwright browsers must be installed via playwright install.

Reference: README.md

- The README includes quick-start steps (venv, dependencies, .env, and running the app), endpoint samples for /search and /eta, and an ASCII architecture overview that aligns with the sections above.
