# 🛒 QuickKart

**Smart grocery price comparison across India's top quick-commerce platforms**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-3.0%2B-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/iamvikkuarya/QuickKart.svg)](https://github.com/iamvikkuarya/QuickKart/stargazers)

> **Never overpay for groceries again!** QuickKart instantly compares prices across Blinkit, Zepto, DMart, and Swiggy Instamart to help you find the best deals with real-time delivery estimates.

---

## ✨ Features

🔍 **Smart Product Matching** - Intelligent fuzzy matching across platforms  
⚡ **Real-time Price Comparison** - Live scraping with 5-minute cache  
📍 **Location-aware Results** - Delivery times based on your location  
🛍️ **4 Major Platforms** - Blinkit, Zepto, DMart & Swiggy Instamart  
🌙 **Modern UI** - Dark/light theme with mobile-first design  
�⚡ **Lightning Fast** - Concurrent scraping for instant results  
💾 **Smart Caching** - Optimized performance with SQLite storage
🛡️ **Rate Limiting** - API protection with Flask-Limiter 

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Maps API key ([Get one here](https://console.cloud.google.com/apis/credentials))

### Installation

```bash
# Clone the repository
git clone https://github.com/iamvikkuarya/QuickKart.git
cd QuickKart

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Setup environment
cp .env.example .env
# Edit .env and add your Google Maps API key
```

### Configuration

1. **Get Google Maps API Key:**
   - Visit [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Enable: Maps JavaScript API, Places API, Geocoding API
   - Create credentials and copy the API key

2. **Update `.env` file:**
   ```env
   GOOGLE_MAPS_API_KEY=your_actual_api_key_here
   ```

### Run the Application

```bash
# Start the server
python run.py

# Or use Flask directly
python app.py
```

Visit `http://localhost:5000` to start comparing prices! 🎉

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask API      │    │   Scrapers      │
│                 │    │                  │    │                 │
│ • Tailwind CSS  │◄──►│ • /search        │◄──►│ • Blinkit       │
│ • Vanilla JS    │    │ • /eta           │    │ • Zepto         │
│ • Google Maps   │    │ • Caching        │    │ • DMart         │
└─────────────────┘    └──────────────────┘    │ • Instamart     │
                                │               └─────────────────┘
                                ▼
                       ┌─────────────────┐
                       │   SQLite DB     │
                       │                 │
                       │ • Products      │
                       │ • Cache         │
                       └─────────────────┘
```

---

## �️ Suppnorted Platforms

### Blinkit
- ⚡ API-based scraping (fastest)
- 📍 Location-aware delivery times
- 🔄 Real-time inventory

### Zepto
- 🌐 Web scraping with Playwright
- ⚡ Fast delivery estimates
- 📦 Wide product range

### DMart Ready
- 🏪 Store-based delivery
- 📅 Slot-based delivery times
- 📍 **Smart Pincode Resolution** - Auto-resolves internal Store IDs
- 💰 Competitive pricing

### Swiggy Instamart (NEW!)
- 🎯 Location-based store selection
- 🗺️ Google Maps geocoding
- ⚡ Quick delivery times
- 📍 Accurate address matching

## 📱 Screenshots

### Home Screen
- Clean, intuitive interface
- Real-time delivery estimates for all 4 platforms
- Location-based results

### Search Results
- Side-by-side price comparison
- Best price highlighting
- Direct links to purchase on each platform

### Smart Features
- Recent search history
- Trending items
- Platform filtering (All/Blinkit/Zepto/DMart/Instamart)

---

## 🔧 API Reference

### Search Products
```http
POST /search
Content-Type: application/json

{
  "query": "milk",
  "address": "Kothrud, Pune",
  "pincode": "411038",
  "latitude": 18.5204,
  "longitude": 73.8567
}
```

**Response:**
```json
[
  {
    "name": "Amul Gold Milk",
    "quantity": "500ml",
    "image_url": "https://...",
    "platforms": [
      {
        "platform": "blinkit",
        "price": "₹28",
        "delivery_time": "12 min",
        "product_url": "https://...",
        "in_stock": true
      }
    ]
  }
]
```

### Get Delivery ETAs
```http
POST /eta
Content-Type: application/json

{
  "address": "Kothrud, Pune",
  "pincode": "411038"
}
```

**Response:**
{
  "blinkit": "12 min",
  "zepto": "15 min", 
  "dmart": "Tomorrow 9 to 11 AM",
  "instamart": "10 min"
}
```

### Get Single Platform ETA
```http
POST /eta_single/<platform>
Content-Type: application/json

{
  "address": "Kothrud, Pune",
  "pincode": "411038"
}
```
*Platform can be: blinkit, zepto, dmart, instamart*

**Response:**
```json
{
  "eta": "12 min",
  "platform": "blinkit"
}
```

### Rate Limiting
- **Default Limit**: 200 requests per day, 60 requests per hour
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## 🛠️ Development

### Project Structure
```
QuickKart/
├── src/
│   ├── scrapers/          # Platform-specific scrapers
│   │   ├── blinkit_scraper.py
│   │   ├── zepto_scraper.py
│   │   ├── dmart_scraper.py
│   │   └── instamart_scraper.py
│   ├── eta/               # Delivery time fetchers
│   │   ├── eta_blinkit.py
│   │   ├── eta_zepto.py
│   │   ├── eta_dmart.py
│   │   └── eta_instamart.py
│   └── core/              # Utilities & database
│       ├── db.py
│       ├── utils.py
│       ├── geocoding.py
│       └── logging_config.py
├── static/                # Frontend assets
├── logs/                  # Application logs (auto-created)
├── app.py                 # Flask application
└── requirements.txt       # Dependencies (pinned versions)
```

### Running in Development Mode

```bash
# Enable debug mode (Windows)
set FLASK_ENV=development
set FLASK_DEBUG=1

# Enable debug mode (macOS/Linux)
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run the app (use_reloader=False to avoid Windows socket errors)
python app.py
```

> **Note:** Logs are saved to `logs/quickkart_YYYY-MM-DD.log`

### Debugging Scrapers

```bash
# Run scrapers in headed mode for debugging
# Edit scraper files and set headless=False
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **🍴 Fork the repository**
2. **🌿 Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **💻 Make your changes**
4. **✅ Test thoroughly**
5. **📝 Commit your changes** (`git commit -m 'Add amazing feature'`)
6. **🚀 Push to the branch** (`git push origin feature/amazing-feature`)
7. **🔄 Open a Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Add comments for complex logic
- Test scrapers with multiple products
- Update documentation for new features

---

## 🐛 Troubleshooting

### Common Issues

**Scrapers returning 0 results:**
- Check if platform websites have changed their structure
- Verify internet connection
- Try running in headed mode for debugging
- For Instamart: Ensure Google Maps API key is configured

**Location detection not working:**
- Ensure Google Maps API key is valid
- Check if required APIs are enabled (Maps JavaScript API, Places API, Geocoding API)
- Verify browser permissions for location access
- Instamart requires accurate geocoding for store selection

**Slow performance:**
- Check cache TTL settings (default: 5 minutes)
- Verify database isn't corrupted
- Monitor network latency
- Playwright browsers may take time on first launch

**Windows socket error (WinError 10038):**
- This is fixed by default with `use_reloader=False`
- If using `FLASK_DEBUG=1`, the reloader is disabled automatically

**Rate Limit Exceeded (429):**
- You have exceeded the API rate limit (200/day or 60/hour)
- Check `Retry-After` header for wait time

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Playwright** - For reliable web scraping
- **Flask** - For the lightweight web framework
- **Tailwind CSS** - For beautiful, responsive design
- **Google Maps** - For location services and geocoding
- **Cloudscraper** - For bypassing Cloudflare protection

---

## 📞 Support

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/iamvikkuarya/QuickKart/issues)
- 💡 **Feature Requests:** [GitHub Discussions](https://github.com/iamvikkuarya/QuickKart/discussions)
- 📧 **Contact:** [vivekkumararya2179@gmail.com](mailto:vivekkumararya2179@gmail.com)

---

<div align="center">

**⭐ Star this repo if QuickKart helped you save money! ⭐**

Made with ❤️ by [Vikku](https://github.com/iamvikkuarya)

</div>
