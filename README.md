# QuickCompare 🛒 — Grocery price comparison (Refactored)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **🚀 NEWLY REFACTORED!** Compare grocery product prices across delivery platforms (Blinkit, Zepto, DMart, Instamart). Clean architecture with professional-grade code structure.

---

## 🏗️ **New Architecture Overview**

The project has been completely refactored with a modern, scalable architecture:

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

## ✨ **What's New**

### 🔥 **Major Improvements**
- **🏗️ Clean Architecture**: Proper separation of concerns
- **📦 Modular Design**: Easy to extend and maintain  
- **🧪 Testable**: Comprehensive test structure
- **⚙️ Configurable**: Environment-based configuration
- **🔄 Backward Compatible**: All existing functionality preserved
- **🚀 Production Ready**: Professional code standards

### 🆕 **New Features**
- **Object-Oriented Scrapers**: Base classes with inheritance
- **Centralized Configuration**: Environment-based settings
- **Advanced Caching**: Thread-safe cache management
- **Data Models**: Proper typing and validation
- **API Structure**: Clean Flask blueprints
- **Setup Scripts**: Easy database initialization
- **Development Tools**: Dev server and utilities

---

## 🚀 **Quick Start**

### **1. Clone & Setup**
```bash
# Clone repository
git clone https://github.com/iamvikkuarya/QuickKart.git
cd QuickKart

# Create virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux  
source .venv/bin/activate
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
pip install playwright
playwright install
```

### **3. Configure Environment**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
GOOGLE_MAPS_API_KEY=your_api_key_here
FLASK_ENV=development
```

### **4. Initialize Database**
```bash
# Using setup script
python scripts/setup_db.py

# Or manually
python -c "from src.core.database import init_db; init_db()"
```

### **5. Run Development Server**
```bash
# Using dev script
python scripts/run_dev.py

# Or directly
python app.py
```

🌐 **Server will start at:** http://127.0.0.1:5000

---

## 📱 **API Endpoints**

### **🔍 Search Products**
```http
POST /search
Content-Type: application/json

{
  "query": "amul milk",
  "address": "Kothrud, Pune",
  "pincode": "411038"
}
```

### **⏱️ Get Delivery ETA**
```http
POST /eta
Content-Type: application/json

{
  "address": "Kothrud, Pune",
  "pincode": "411038"
}
```

### **⚙️ Get Configuration**
```http
GET /config
```

---

## 🛠️ **Development**

### **🏗️ Project Structure**

#### **Core Components**
- **`src/core/`**: Database, caching, and utility functions
- **`src/scrapers/`**: Platform-specific scrapers with base class
- **`src/eta/`**: ETA fetchers for each platform
- **`src/api/`**: Flask routes and business logic handlers
- **`src/models/`**: Data models and location services

#### **Configuration**
- **`config/settings.py`**: Centralized configuration management
- **`.env`**: Environment variables (create from `.env.example`)

#### **Scripts**
- **`scripts/setup_db.py`**: Initialize database
- **`scripts/run_dev.py`**: Development server

### **🧪 Running Tests**
```bash
# Run scraper tests
python tests/test_scrapers/test_blinkit.py

# Run API tests
python tests/test_api/test_routes.py

# Setup test database
python scripts/setup_db.py --cleanup
```

### **🎨 Code Style**
The codebase follows modern Python patterns:
- **Type hints** for better IDE support
- **Dataclasses** for clean data structures  
- **Abstract base classes** for consistent interfaces
- **Dependency injection** for testability
- **Environment-based configuration**

---

## 📊 **Product Schema**

Products are normalized across all platforms:

```json
{
  "platform": "blinkit | zepto | dmart | instamart",
  "name": "Amul Gold Full Cream Milk",
  "price": "₹66",
  "quantity": "1L",
  "image_url": "https://...",
  "product_url": "https://...",
  "delivery_time": "12 min",
  "in_stock": true
}
```

**Merged Response:**
```json
{
  "name": "Amul Gold Full Cream Milk",
  "quantity": "1L", 
  "image_url": "https://...",
  "platforms": [
    {
      "platform": "blinkit",
      "price": "₹66",
      "delivery_time": "12 min",
      "product_url": "https://...",
      "in_stock": true
    },
    {
      "platform": "zepto", 
      "price": "₹64",
      "delivery_time": "10 min",
      "product_url": "https://...",
      "in_stock": true
    }
  ]
}
```

---

## ⚙️ **Configuration Options**

### **Environment Variables**
```bash
# Flask Settings
FLASK_ENV=development|production
FLASK_DEBUG=true|false
HOST=127.0.0.1
PORT=5000

# External Services
GOOGLE_MAPS_API_KEY=your_key

# Database
DATABASE_NAME=product.db

# Caching (seconds)
CACHE_TTL=300

# Defaults
DEFAULT_ADDRESS=Kothrud, Pune
DEFAULT_PINCODE=411038
```

### **Programmatic Configuration**
```python
from config.settings import get_config

config = get_config()
print(f"Environment: {config.environment}")
print(f"Debug mode: {config.is_development()}")
```

---

## 🔧 **Advanced Usage**

### **Custom Scrapers**
```python
from src.scrapers.base import BaseScraper

class CustomScraper(BaseScraper):
    def get_platform_name(self) -> str:
        return "custom"
    
    def build_search_url(self, query: str) -> str:
        return f"https://example.com/search?q={query}"
    
    def parse_products(self, page) -> List[Dict[str, Any]]:
        # Custom parsing logic
        return []
```

### **Database Operations**
```python
from src.core.database import DatabaseManager

db = DatabaseManager()
db.init_db()

# Get recent products
recent = db.get_recent_products(hours=24)

# Cleanup old data
deleted = db.cleanup_old_products(days=7)
```

### **Cache Management**
```python
from src.core.cache import search_cache, eta_cache

# Manual cache operations
search_cache.set_search_results("milk", "pune", "411038", results)
cached = search_cache.get_search_results("milk", "pune", "411038")
```

---

## 🤝 **Contributing**

We welcome contributions! The new architecture makes it much easier:

1. **🍴 Fork** the repository
2. **🌿 Create** a feature branch
3. **✅ Add tests** for new functionality  
4. **🔧 Follow** existing code patterns
5. **📝 Update** documentation
6. **🚀 Submit** a pull request

### **Adding New Platforms**
1. Inherit from `BaseScraper` and `BaseETA`
2. Implement required methods
3. Add to handlers and routes
4. Create tests

---

## 🐛 **Troubleshooting**

### **Common Issues**
- **Import Errors**: Make sure you're in the project root
- **Database Errors**: Run `python scripts/setup_db.py`
- **Scraping Fails**: Check if websites have changed selectors
- **Cache Issues**: Clear cache or restart the server

### **Debug Mode**
```bash
FLASK_ENV=development FLASK_DEBUG=true python app.py
```

---

## 📈 **Performance**

- **⚡ Concurrent Scraping**: All platforms scraped in parallel
- **🗄️ Smart Caching**: 5-minute TTL with automatic cleanup
- **💾 Database Indexing**: Optimized queries
- **🧵 Thread Safety**: Safe for concurrent requests

---

## 📄 **License**

MIT © Vikku

---

## 🙏 **Acknowledgments**

- **🎭 Playwright**: Web scraping framework
- **🌶️ Flask**: Web framework
- **🔍 RapidFuzz**: Fuzzy string matching  
- **🗄️ SQLite**: Database
- **🐍 Python**: Programming language

---

> **💡 Pro Tip**: The refactored codebase is production-ready and follows industry best practices. Perfect for learning modern Python architecture!

**⭐ Star this repo if you found it helpful!**