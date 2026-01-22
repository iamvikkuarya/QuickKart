<div align="center">

# 🛒 QuickKart

**Smart grocery price comparison across India's top quick-commerce platforms**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Playwright](https://img.shields.io/badge/playwright-45ba4b?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br />

> **Stop overpaying for groceries.**  
> QuickKart instantly compares prices across **Blinkit**, **Zepto**, **DMart**, and **Swiggy Instamart** to help you find the best deals with real-time delivery estimates.

[Features](#-features) • [Installation](#-quick-start) • [API](#-api-reference) • [Contributing](#-contributing)

---
</div>

## ✨ Features

QuickKart is built for speed and accuracy.

| | |
|---|---|
| 🔍 **Smart Matching**<br>Fuzzy matching algorithms ensure accurate product comparisons across different platform naming conventions. | ⚡ **Real-time Engine**<br>Live scraping engine fetches fresh prices and inventory status in seconds, backed by a 5-minute cache. |
| 📍 **Location Intelligence**<br> precise delivery estimates and store selection based on your exact geolocation using Google Maps. | �️ **Rate Limiting**<br>Enterprise-grade API protection using Flask-Limiter to ensure stability and fair usage (200 req/day). |
| 🛍️ **Multi-Platform**<br>Simultaneous support for Blinkit, Zepto, DMart Ready, and Swiggy Instamart. | 🚀 **High Performance**<br>Concurrent execution and SQLite optimizations for lightning-fast responses. |

<br/>

## 🏗️ Tech Stack

<div align="center">

| Backend | Scraping | Frontend | Data/Ops |
| :---: | :---: | :---: | :---: |
| **Flask** | **Playwright** | **Tailwind CSS** | **SQLite** |
| Python 3.10+ | BeautifulSoup4 | Vanilla JS | Google Maps API |
| Flask-Limiter | Cloudscraper | HTML5 | Dotenv |

</div>

---

## 🚀 Quick Start

### Prerequisites
*   **Python 3.10+**
*   **Google Maps API Key** (Required for location services)
    *   *APIs needed: Maps JavaScript, Places, Geocoding*

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/iamvikkuarya/QuickKart.git
cd QuickKart

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
playwright install

# 4. Configure Environment
cp .env.example .env
# Open .env and add your GOOGLE_MAPS_API_KEY
```

### Running the App

```bash
# Start the customized server script
python run.py

# Access the UI at http://localhost:5000
```

---

## 🔌 Supported Platforms

| Platform | Type | Key Features |
| :--- | :--- | :--- |
| **Blinkit** | API / Web | ⚡ Fast API-based scraping, real-time inventory. |
| **Zepto** | Web (Playwright) | 🌐 Headless browser scraping, accurate delivery ETAs. |
| **DMart** | Store / Slots | 📍 **Smart Pincode Resolution** to find nearest store & slots. |
| **Instamart** | Location | 🎯 Precise address matching via Google Geocoding. |

---

## � API Reference

QuickKart exposes a RESTful API for search and logistics.

### 🔍 Search Products
`POST /search`

Searches all platforms for a given query at a specific location.

<details>
<summary><b>View Request/Response Example</b></summary>

**Request:**
```json
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
    "platforms": [
      {
        "platform": "blinkit",
        "price": "₹28",
        "delivery_time": "12 min",
        "in_stock": true
      }
    ]
  }
]
```
</details>

### 🚚 Get Delivery ETAs
`POST /eta`

Fetches delivery estimates for all platforms simultaneously.

<details>
<summary><b>View Request/Response Example</b></summary>

**Request:**
```json
{
  "address": "Kothrud, Pune",
  "pincode": "411038"
}
```

**Response:**
```json
{
  "blinkit": "12 min",
  "zepto": "15 min", 
  "dmart": "Tomorrow 9-11 AM",
  "instamart": "10 min"
}
```
</details>

### ⏱️ Single Platform ETA
`POST /eta_single/<platform>`

Check ETA for a specific platform (`blinkit`, `zepto`, `dmart`, `instamart`).

---

## 🐛 Troubleshooting

| Issue | Solution |
| :--- | :--- |
| **Scrapers returning 0 results** | Check internet, try `headless=False` in scraper files to debug. |
| **Location errors** | Verify your Google Maps API Key has *Geocoding* and *Places* enabled. |
| **Rate Limit (429)** | You hit the 200/day limit. Wait or check headers for reset time. |
| **WinError 10038** | Ignore, or ensure `use_reloader=False` is set (default in `run.py`). |

---

## 🤝 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

<div align="center">

### License

Distributed under the MIT License. See `LICENSE` for more information.

**[Vikku](https://github.com/iamvikkuarya) • 2026**

</div>
