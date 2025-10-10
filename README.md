# QuickCompare 🛒 — Smart Grocery Price Comparison

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Flask](https://img.shields.io/badge/flask-2.3%2B-green)](https://flask.palletsprojects.com/)

QuickCompare is a powerful web application that helps you find the best deals on groceries by comparing prices and delivery times across major Indian delivery platforms including Blinkit, Zepto, DMart, and Instamart. Never overpay for groceries again!

## 🎯 **What Does QuickCompare Do?**

- **💰 Price Comparison**: Automatically searches for products across multiple platforms and shows you the best prices
- **⏰ Delivery Time**: Compares delivery ETAs so you can choose based on urgency
- **🔍 Smart Search**: Intelligently matches similar products across different platforms
- **📍 Location-Aware**: Uses your location to provide accurate pricing and delivery estimates
- **🚀 Real-Time**: Fresh data scraped in real-time, no outdated information

---

## 🏗️ **Project Structure**

QuickCompare is built with a clean, modular architecture that makes it easy to maintain and extend:

```
quickcompare/
├── 📁 src/                          # Main source code
│   ├── 🔧 core/                     # Core utilities
│   │   ├── database.py              # Database management
│   │   ├── utils.py                 # Product processing utilities
│   │   └── cache.py                 # Caching system
│   ├── 🕷️ scrapers/                 # Web scrapers
│   │   ├── base.py                  # Base scraper class
│   │   ├── blinkit.py               # Blinkit scraper
│   │   ├── zepto.py                 # Zepto scraper
│   │   ├── dmart.py                 # DMart scraper
│   │   └── instamart.py             # Instamart scraper
│   ├── ⏱️ eta/                      # ETA fetchers
│   │   ├── base.py                  # Base ETA class
│   │   ├── blinkit.py               # Blinkit ETA
│   │   ├── zepto.py                 # Zepto ETA
│   │   ├── dmart.py                 # DMart ETA
│   │   └── instamart.py             # Instamart ETA
│   ├── 🌐 api/                      # Flask API
│   │   ├── routes.py                # API routes
│   │   └── handlers.py              # Business logic
│   └── 📊 models/                   # Data models
│       ├── product.py               # Product models
│       └── location.py              # Location services
├── ⚙️ config/                       # Configuration
│   └── settings.py                  # Centralized settings
├── 🧪 tests/                        # Test suite
├── 📜 scripts/                      # Utility scripts
├── 📁 static/                       # Frontend assets
└── 📄 app.py                        # Application entry point
```

---

## ⭐ **Key Features**

### 🛍️ **For Shoppers**
- **Multi-Platform Search**: Compare prices across Blinkit, Zepto, DMart, and more
- **Location-Based Results**: Accurate pricing and delivery times for your area
- **Smart Product Matching**: Automatically groups same products from different platforms
- **Visual Interface**: Clean, easy-to-use web interface with platform logos and filters
- **Real-Time ETAs**: See delivery times for each platform before you order

### 🛠️ **For Developers**
- **Professional Architecture**: Clean separation of concerns with modular design
- **Easy to Extend**: Add new platforms by implementing simple base classes
- **Robust Caching**: Smart caching system to avoid unnecessary requests
- **RESTful API**: Well-designed API endpoints for integration
- **Comprehensive Testing**: Test suite for reliable functionality
- **Environment Configuration**: Easy setup for different deployment environments

---

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.10 or higher
- Google Maps API key (for location services)

### **1. Clone & Setup**
```bash
# Clone the repository
git clone https://github.com/iamvikkuarya/QuickKart.git
cd QuickKart

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Mac/Linux:
source .venv/bin/activate
```

### **2. Install Dependencies**
```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### **3. Configure Environment**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Google Maps API key:
GOOGLE_MAPS_API_KEY=your_actual_api_key_here
```

### **4. Initialize Database**
```bash
# Set up the database
python scripts/setup_db.py
```

### **5. Start the Application**
```bash
# Run the development server
python scripts/run_dev.py

# Or start directly
python app.py
```

🌐 **Open your browser and visit:** http://127.0.0.1:5000

That's it! You can now search for grocery products and compare prices across platforms.

---

## 🖥️ **How to Use QuickCompare**

### **Web Interface**
1. **🔍 Search**: Type any grocery item (e.g., "amul milk", "bread", "rice")
2. **📍 Location**: The app automatically detects your location for accurate results
3. **⚖️ Compare**: See prices, delivery times, and availability across platforms
4. **🎯 Filter**: Use platform filters to focus on specific delivery services
5. **🛒 Shop**: Click on any result to go directly to the product page

### **API Endpoints**
For developers who want to integrate QuickCompare:

#### **Search Products**
```http
POST /search
Content-Type: application/json

{
  "query": "amul milk",
  "address": "Kothrud, Pune",
  "pincode": "411038"
}
```

#### **Get Delivery Times**
```http
POST /eta
Content-Type: application/json

{
  "address": "Kothrud, Pune",
  "pincode": "411038"
}
```

---

## 🧠 **How It Works**

### **Behind the Scenes**
1. **Web Scraping**: When you search, QuickCompare simultaneously visits each platform's website
2. **Smart Parsing**: Extracts product names, prices, quantities, and images from each site
3. **Product Matching**: Uses fuzzy matching algorithms to group similar products together
4. **Location Services**: Uses Google Maps API to get accurate delivery times for your area
5. **Caching**: Stores recent results to provide faster responses
6. **Database**: Saves all product data for analytics and performance

### **Supported Platforms**
- 🟢 **Blinkit**: 10-minute grocery delivery
- 🟣 **Zepto**: Ultra-fast delivery service
- 🟡 **DMart**: DMart Ready - online grocery
- 🔵 **Instamart**: Swiggy's grocery delivery

### **Technical Architecture**
- **Backend**: Python Flask with concurrent web scraping
- **Frontend**: Clean HTML/CSS/JavaScript interface
- **Database**: SQLite for product storage
- **Caching**: In-memory caching for performance
- **Location**: Google Maps API integration

---

## 🛠️ **For Developers**

### **Project Structure**
```
quickcompare/
├── 📁 src/                    # Main source code
│   ├── 🔧 core/               # Database, caching, utilities
│   ├── 🕷️ scrapers/           # Platform scrapers (Blinkit, Zepto, etc.)
│   ├── ⏱️ eta/                # Delivery time fetchers
│   ├── 🌐 api/                # Flask routes and handlers
│   └── 📊 models/             # Data models and schemas
├── ⚙️ config/                 # Configuration management
├── 🧪 tests/                  # Test suite
├── 📜 scripts/                # Utility scripts
├── 📁 static/                 # Frontend files (HTML, CSS, JS)
└── 📄 app.py                  # Application entry point
```

### **Adding New Platforms**
To add support for a new grocery platform:

1. **Create a scraper** in `src/scrapers/`:
```python
from .base import BaseScraper

class NewPlatformScraper(BaseScraper):
    def get_platform_name(self) -> str:
        return "newplatform"
    
    def build_search_url(self, query: str) -> str:
        return f"https://newplatform.com/search?q={query}"
    
    def parse_products(self, page) -> List[Dict[str, Any]]:
        # Extract products from the page
        return products
```

2. **Create an ETA fetcher** in `src/eta/`:
```python
from .base import BaseETA

class NewPlatformETA(BaseETA):
    # Implementation for delivery time fetching
```

3. **Add to handlers** in `src/api/handlers.py`
4. **Update frontend** to include the new platform

### **Running Tests**
```bash
# Test scrapers
python -m pytest tests/test_scrapers/

# Test API endpoints
python -m pytest tests/test_api/

# Test specific component
python tests/test_scrapers/test_blinkit.py
```

---

## ⚙️ **Configuration**

### **Environment Variables (.env file)**
```env
# Required: Google Maps API key for location services
GOOGLE_MAPS_API_KEY=your_api_key_here

# Application settings
FLASK_ENV=development
FLASK_DEBUG=true
HOST=127.0.0.1
PORT=5000

# Database settings
DATABASE_NAME=product.db

# Cache duration (in seconds)
CACHE_TTL=300

# Default location (used as fallback)
DEFAULT_ADDRESS=Kothrud, Pune
DEFAULT_PINCODE=411038
```

### **Google Maps API Setup**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the "Maps JavaScript API" and "Geocoding API"
4. Create credentials (API key)
5. Add the API key to your `.env` file

---

## 🔧 **Advanced Features**

### **Smart Product Matching**
QuickCompare uses intelligent algorithms to match similar products:
- **Quantity Normalization**: "1L", "1 Litre", "1000ml" are recognized as the same
- **Brand Recognition**: Matches products from the same brand across platforms
- **Fuzzy Name Matching**: Handles variations in product names
- **Price Validation**: Filters out unrealistic prices

### **Caching System**
- **Search Results**: Cached for 5 minutes to avoid repetitive scraping
- **ETA Data**: Delivery times cached to reduce API calls
- **Automatic Cleanup**: Old cache entries are automatically removed

### **Database Management**
```bash
# Initialize database
python scripts/setup_db.py

# Clean old data
python scripts/setup_db.py --cleanup

# View database stats
python -c "from src.core.database import DatabaseManager; db = DatabaseManager(); print('Total products:', db.get_recent_products(hours=24*365).__len__())"
```

---

## 🤝 **Contributing**

Contributions are welcome! Here's how you can help:

### **Ways to Contribute**
- 🐛 **Bug Reports**: Found an issue? Report it!
- 🆕 **New Platforms**: Add support for more grocery delivery services
- 🎨 **UI Improvements**: Enhance the user interface
- ⚡ **Performance**: Optimize scraping or caching
- 📖 **Documentation**: Improve documentation and examples

### **Development Process**
1. **Fork** the repository
2. **Clone** your fork locally
3. **Create** a feature branch: `git checkout -b feature-name`
4. **Make** your changes and test them
5. **Commit** with descriptive messages
6. **Push** to your fork and create a Pull Request

### **Code Guidelines**
- Follow existing code style and structure
- Add tests for new functionality
- Update documentation as needed
- Test your changes thoroughly

---

## 🐛 **Troubleshooting**

### **Common Issues**

**❌ "No products found"**
- Check your internet connection
- Try a different search term
- Ensure the platforms deliver to your area

**❌ Location not detected**
- Check if browser location permission is enabled
- Verify your Google Maps API key is correct
- Try manually setting your location in the .env file

**❌ App won't start**
- Ensure Python 3.10+ is installed
- Check if all dependencies are installed: `pip install -r requirements.txt`
- Initialize the database: `python scripts/setup_db.py`

**❌ Scraping errors**
- Websites may have changed their structure
- Check if you're being rate-limited
- Try running in non-headless mode for debugging

### **Getting Help**
- Check existing issues on GitHub
- Create a new issue with detailed error information
- Include your Python version, OS, and error logs

## 📜 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 **Acknowledgments**

- **Playwright**: For reliable web scraping capabilities
- **Flask**: For the lightweight web framework
- **RapidFuzz**: For intelligent product matching
- **Google Maps**: For location services
- **All grocery platforms**: For making their services available

---

## ⭐ **Show Your Support**

If QuickCompare helped you save money on groceries, please consider:
- ⭐ Starring this repository
- 🐛 Reporting bugs or requesting features
- 🤝 Contributing to the codebase
- 📢 Sharing with friends who love good deals!

---

**Made with ❤️ for smart shoppers who love great deals!**

*Happy shopping! 🛒*
