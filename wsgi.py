#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""

import os
from app import app

# This is what WSGI servers will import
application = app

if __name__ == "__main__":
    # For local testing
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)