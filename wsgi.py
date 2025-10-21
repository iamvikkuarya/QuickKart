#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""

import os
from src.core.db import init_db
from app import app

# Initialize database if it doesn't exist
if not os.path.exists("product.db"):
    print("🔧 Initializing database...")
    init_db()
    print("✅ Database initialized")

# This is what WSGI servers will import
application = app

if __name__ == "__main__":
    # For local testing
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)