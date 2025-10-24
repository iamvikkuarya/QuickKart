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
    
    # Get port from environment (Railway sets this)
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV", "development") == "development"
    
    print("🚀 Starting QuickKart server...")
    print("📍 Make sure to add your Google Maps API key to environment variables")
    print(f"🌐 Server will be available on port: {port}")
    
    app.run(debug=debug_mode, host="0.0.0.0", port=port)