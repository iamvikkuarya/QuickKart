#!/bin/bash
# Render build script

set -e

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🌐 Installing Playwright browsers..."
playwright install chromium --with-deps

echo "✅ Build complete!"