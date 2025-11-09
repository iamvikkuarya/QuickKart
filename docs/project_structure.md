# QuickKart Project Structure

```
QuickKart/
├── src/                          # Source code
│   ├── __init__.py
│   ├── scrapers/                 # Platform scrapers
│   │   ├── blinkit_scraper.py   # Blinkit API scraper
│   │   ├── zepto_scraper.py     # Zepto API scraper (optimized)
│   │   ├── dmart_scraper.py     # DMart API scraper
│   │   ├── dmart_location.py    # DMart location utilities
│   │   └── instamart_scraper.py # Instamart scraper
│   ├── eta/                      # ETA fetchers
│   │   ├── eta_blinkit.py
│   │   ├── eta_zepto.py
│   │   ├── eta_dmart.py
│   │   └── eta_instamart.py
│   └── core/                     # Core utilities
│       ├── __init__.py
│       ├── utils.py              # Product merging & comparison logic
│       └── db.py                 # Database operations
├── static/                       # Frontend assets
│   ├── index.html                # Main UI
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── app.js                # Frontend logic
│   └── assets/                   # Platform logos & images
│       ├── Blinkit_logo.webp
│       ├── zepto_logo.webp
│       ├── Dmart_logo.webp
│       └── instamart_logo.png
├── docs/                         # Documentation
│   └── project_structure.md
├── comparison-test/              # Testing for comparison logic
├── zepto-research/               # Research & optimization tests
├── app.py                        # Flask application
├── run.py                        # Application runner
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (not in git)
├── .gitignore
└── README.md
```

## Module Descriptions

### `src/scrapers/`
Platform-specific scrapers that extract product data:
- **blinkit_scraper.py**: Direct API scraper for Blinkit
- **zepto_scraper.py**: Optimized API interceptor (60% faster than DOM scraping)
- **dmart_scraper.py**: API-based scraper for DMart
- **dmart_location.py**: Store ID resolution by pincode
- **instamart_scraper.py**: Swiggy Instamart scraper

### `src/eta/`
ETA (Estimated Time of Arrival) fetchers:
- **eta_blinkit.py**: Delivery time from Blinkit
- **eta_zepto.py**: Delivery time from Zepto
- **eta_dmart.py**: Delivery slots from DMart
- **eta_instamart.py**: Delivery time from Instamart

### `src/core/`
Core application utilities:
- **utils.py**: 
  - Improved product merging with fuzzy matching
  - Quantity normalization (handles ml, l, g, kg, gm, etc.)
  - Brand extraction (30+ known brands)
  - Price analysis with savings calculation
- **db.py**: SQLite database operations and schema

### Frontend (`static/`)
- **index.html**: Main UI with dark mode support
- **app.js**: Search, filtering, location detection, product rendering
- **styles.css**: Custom styling and theme variables

### Root Files
- **app.py**: Main Flask application with API endpoints
- **run.py**: Application entry point with DB initialization
- **requirements.txt**: Python package dependencies
- **.env**: Environment variables (Google Maps API key, etc.)

## Key Features

### Optimized Scraping
- Zepto scraper uses API interception (~4s vs ~10s)
- All scrapers use headless browsers or direct API calls
- Concurrent scraping with ThreadPoolExecutor

### Smart Product Matching
- Fuzzy name matching with RapidFuzz
- Quantity normalization and comparison
- Brand-aware matching
- 10% tolerance for quantity variations

### Caching
- 5-minute cache for search results
- 5-minute cache for ETA data
- Location caching (7 days)

### UI Features
- Dark/light mode toggle
- Real-time ETA updates
- Platform filtering
- Best deal highlighting (green border)
- Out of stock indicators
- Responsive design
