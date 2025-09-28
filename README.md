QuickKart
QuickKart is a Python-based web application for comparing product prices and delivery ETAs across major Indian online grocery platforms. It enables users to search for grocery items and compare availability, prices, and estimated delivery times from Blinkit, Zepto, and Dmart, with results being merged and normalized for best user experience.

Features
Price and availability comparison for products across Blinkit, Zepto, and Dmart

Location-aware ETA estimates for each platform

Automatic data merging and normalization to present the most relevant product matches

Caching for faster repeated queries and efficiency

Modern web interface (HTML/Tailwind CSS, see static/index.html)

SQLite database for storing product snapshots

How it Works
User searches for a grocery product by name.

QuickKart scrapes search results (name, quantity, price, link, image, stock) from Blinkit and Zepto, and (with store location detection) from Dmart.

Results are merged to unify listings for the same product, normalizing quantities and prices.

ETAs for each vendor are fetched (location aware).

The result—a unified listing of all platforms with prices, links, and estimated delivery times—is shown.

File Structure
app.py - Flask backend, manages HTTP routes (/search, /eta, /config) and orchestrates scrapers and merge logic

blinkit_scraper.py, zepto_scraper.py, dmart_scraper.py - Platform-specific web scrapers using Playwright & BeautifulSoup

dmart_location.py - Fetches Dmart store details by user pincode

eta_blinkit.py, eta_zepto.py, eta_dmart.py - ETAs for each platform

utils.py - Product merging, normalization, and matching logic

db.py - SQLite schema (product.db) and helper functions

static/ - Frontend HTML assets (main: index.html)

.gitignore, requirements.txt (if present) - Development environment and dependency management

Requirements
Python 3.8+

Playwright (and browser drivers)

Flask

sqlite3

BeautifulSoup4

rapidfuzz

requests

python-dotenv (optional, for .env configs)

You can install requirements with:

bash
pip install flask playwright beautifulsoup4 rapidfuzz requests python-dotenv
playwright install
Usage
Clone the repository:

bash
git clone https://github.com/iamvikkuarya/QuickKart
cd QuickKart
Install dependencies:

text
pip install -r requirements.txt
playwright install
(Optional) Configure environment:

Set up .env to include GOOGLE_MAPS_API_KEY if using the /config endpoint.

Run the application:

text
python app.py
The app will be served on localhost (default: port 5000).

Open frontend:

Open static/index.html in your web browser, or access via the Flask server route.

Endpoints
/search (POST): Search for product across platforms. Payload: { "query": "amul milk", "address": "...", "pincode": "..." }

/eta (POST): Get delivery ETAs for address/pincode.

/config (GET): Get config details.

Database
SQLite database (product.db) stores raw scraped products in a products table:

id, name, quantity, platform, price, product_url, image_url, in_stock, scraped_at

Development Notes
Caching is used for both product and ETA queries (configurable time-to-live).

The project supports rapid development; modify or add new scrapers for more platforms as needed.

Contributing
Fork the repository and submit pull requests.

Please lint and test your code before submission.