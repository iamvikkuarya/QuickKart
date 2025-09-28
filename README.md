# QuickKart 🛒 — Grocery price comparison (Blinkit & Zepto)

[![CI](https://github.com/iamvikkuarya/QuickKart/actions/workflows/ci.yml/badge.svg)](https://github.com/iamvikkuarya/QuickKart/actions)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](#)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> Compare grocery product prices across delivery platforms (Blinkit, Zepto). Proof‑of‑concept scrapers + ETA fetchers with a simple Flask frontend.

---

## Table of contents

- [Why QuickKart](#why-quickkart)
- [Features](#features)
- [Quick start](#quick-start)
- [Usage (API)](#usage-api)
- [Architecture](#architecture)
- [Product schema](#product-schema)
- [Configuration](#configuration)
- [Development notes](#development-notes)
- [Contributing](#contributing)
- [License](#license)

---

## Why QuickKart

QuickKart helps you instantly compare grocery items across Blinkit and Zepto by scraping product listings and normalizing them into a single format, plus showing delivery ETA per platform — useful for price/availability comparisons and building a better shopping UI.

---

## Features

- Playwright-based scrapers for Blinkit & Zepto.  
- Normalized product schema for easy comparison.  
- Per-platform delivery ETA fetchers.  
- Flask backend with caching and SQLite persistence.  
- Lightweight SPA frontend (Tailwind) with location detection.

--- 

## Quick start

```bash
# clone
git clone https://github.com/iamvikkuarya/QuickKart.git
cd QuickKart

# python venv
python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows
.venv\\Scripts\\activate

# install deps
pip install -r requirements.txt
# if using Playwright (required for scrapers):
pip install playwright
playwright install

# create .env in project root (example)
cat > .env <<EOF
GOOGLE_MAPS_API_KEY=YOUR_BROWSER_MAPS_KEY
FLASK_ENV=development
EOF

# run (development)
export FLASK_APP=app.py
flask run --reload
# or
python app.py
```

---

## Usage (API)

- `POST /search`  
  Request JSON:  
  ```json
  { "query": "milk", "latitude": 18.5204, "longitude": 73.8567, "address": "Kothrud, Pune" }
  ```
  Response: merged list of normalized product objects from Blinkit & Zepto.

- `POST /eta`  
  Request JSON:
  ```json
  { "address": "Kothrud, Pune", "pincode": "411038" }
  ```
  Response: ETA info per supported platform.

---

## Architecture

```
Frontend (Tailwind SPA)
   ↕
Flask backend (app.py)
   ↕
Scrapers (blinkit_scraper.py, zepto_scraper.py)  -- Playwright
ETA fetchers (eta_blinkit.py, eta_zepto.py)
DB: SQLite (product.db)
```

Key notes:
- Scrapers return a normalized JSON schema so results can be merged/compared on the frontend.
- Caching: in-memory caches for search results and ETA with short TTL (default 5 minutes).

---

## Product schema

All scrapers return objects normalized to:

```json
{
  "platform": "blinkit | zepto",
  "name": "Product Name",
  "price": "₹123",
  "quantity": "500 ml",
  "image_url": "https://...",
  "product_url": "https://...",
  "delivery_time": "N/A",
  "in_stock": true
}
```

---

## Configuration

- Create `.env` for secrets (do **not** commit it). Add `.env` to `.gitignore`.

Example `.env`:
```
GOOGLE_MAPS_API_KEY=AIza...
FLASK_ENV=development
```

**Maps key guidance:** the Maps JavaScript key must be usable in the browser, so restrict it by **HTTP referrers** in Google Cloud Console (your deployment domain). For server-side Google APIs (if used), use a separate server key restricted by your server IP.

---

## Development notes & debugging tips

- Playwright: for debugging selectors run in headed mode (`headful`) and open devtools; this makes it easier to inspect Blinkit / Zepto DOM structure.  
- If you get `0 products` returned: confirm search page scrolled enough and selectors are accurate — try manual browsing in headed Playwright to identify selector changes.  
- Keep scrapers robust: add retry logic, dynamic timeouts, and short backoff for flaky selectors.

---

## Tests & CI

Add GitHub Actions to run `pytest` and (optionally) build docs. Example workflow file path: `.github/workflows/ci.yml`.

---

## Contributing

Contributions welcome — open issues/PRs.  
Please follow these steps:

1. Fork → branch → implement.
2. Run tests and linters locally.
3. Open a PR with description and testing notes.

See `CONTRIBUTING.md` for more.

---

## Screenshots & GIFs guidelines

- Put images under `docs/images/` (or `assets/`) and reference them in README.
- Keep GIFs short (3–6s) and compressed; prefer a short MP4 if file size matters.

---

## License

MIT © Vikku
