#!/bin/bash
# Render build script

set -e

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🌐 Installing Playwright browsers..."
playwright install chromium
playwright install-deps chromium

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