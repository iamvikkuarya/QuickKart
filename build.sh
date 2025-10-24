#!/bin/bash

echo "🔧 Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "🎭 Installing Playwright browsers..."
playwright install --with-deps chromium

echo "✅ Build completed successfully!"