#!/usr/bin/env python3
"""
Development server runner for QuickCompare.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_development_server():
    """Run the development server with proper configuration."""
    print("🚀 Starting QuickCompare development server...")
    
    # Set development environment
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = 'true'
    
    try:
        # Import and run the app
        from app import app
        from src.core.database import init_db
        
        # Initialize database
        print("🔧 Initializing database...")
        init_db()
        print("✅ Database ready!")
        
        # Start the server
        print("🌐 Server starting on http://127.0.0.1:5000")
        print("📱 API endpoints available:")
        print("   - GET  /config")
        print("   - POST /search") 
        print("   - POST /eta")
        print("   - GET  /")
        print("\n💡 Press CTRL+C to stop the server\n")
        
        app.run(
            debug=True,
            host='127.0.0.1',
            port=5000,
            use_reloader=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_development_server()