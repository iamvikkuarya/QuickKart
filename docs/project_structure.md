# QuickKart Project Structure

```
QuickKart/
├── src/                          # Source code
│   ├── __init__.py
│   ├── scrapers/                 # Platform scrapers
│   │   ├── blinkit_scraper.py
│   │   ├── zepto_scraper.py
│   │   ├── dmart_scraper.py
│   │   └── dmart_location.py
│   ├── eta/                      # ETA fetchers
│   │   ├── eta_blinkit.py
│   │   ├── eta_zepto.py
│   │   └── eta_dmart.py
│   └── core/                     # Core utilities
│       ├── __init__.py
│       ├── utils.py              # Product merging logic
│       └── db.py                 # Database operations
├── static/                       # Frontend assets
│   ├── index.html
│   └── assets/
│       ├── blinkit.png
│       ├── zepto.png
│       └── dmart.png
├── docs/                         # Documentation
│   └── project_structure.md
├── app.py                        # Flask application
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
├── .gitignore
└── README.md
```

## Module Descriptions

### `src/scrapers/`
Contains platform-specific scrapers that extract product data:
- **blinkit_scraper.py**: Scrapes Blinkit using Playwright
- **zepto_scraper.py**: Scrapes Zepto using Playwright  
- **dmart_scraper.py**: Scrapes DMart using API calls
- **dmart_location.py**: DMart location resolution utilities

### `src/eta/`
Contains ETA (Estimated Time of Arrival) fetchers:
- **eta_blinkit.py**: Fetches delivery time from Blinkit
- **eta_zepto.py**: Fetches delivery time from Zepto
- **eta_dmart.py**: Fetches delivery slots from DMart

### `src/core/`
Core application utilities:
- **utils.py**: Product merging, quantity normalization, fuzzy matching
- **db.py**: SQLite database operations and schema

### Root Files
- **app.py**: Main Flask application with API endpoints
- **requirements.txt**: Python package dependencies
- **.env**: Environment variables (API keys, etc.)