#!/bin/bash
# Render build script

set -e

echo "📦 Installing system dependencies..."
apt-get update
apt-get install -y wget gnupg ca-certificates

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🌐 Installing Playwright browsers with system dependencies..."
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright
playwright install --with-deps chromium

echo "🔧 Initializing database..."
python -c "
import os
from src.core.db import init_db
if not os.path.exists('product.db'):
    init_db()
    print('✅ Database initialized')
else:
    print('✅ Database already exists')
"

echo "✅ Build complete!"