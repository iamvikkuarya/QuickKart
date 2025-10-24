#!/bin/bash

# Initialize database if it doesn't exist
python -c "
import os
from src.core.db import init_db

if not os.path.exists('product.db'):
    print('🔧 Initializing database...')
    init_db()
    print('✅ Database initialized')
else:
    print('📦 Database already exists')
"

# Start Gunicorn with proper port handling
PORT=${PORT:-5000}
echo "🚀 Starting Gunicorn on port $PORT"
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile - app:app