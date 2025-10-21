#!/usr/bin/env python3
"""
QuickKart - Grocery Price Comparison Tool
Simple runner script for the Flask application
"""

import os
from src.core.db import init_db
from app import app

if __name__ == "__main__":
    # Initialize database if it doesn't exist
    if not os.path.exists("product.db"):
        print("🔧 Initializing database...")
        init_db()
        print("✅ Database initialized")
    
    print("🚀 Starting QuickKart server...")
    print("📍 Make sure to add your Google Maps API key to .env file")
    print("🌐 Server will be available at: http://localhost:5000")
    
    app.run(debug=True, host="0.0.0.0", port=5000)