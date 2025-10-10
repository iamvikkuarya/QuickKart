"""
QuickCompare Flask Application - Main Entry Point
"""

import os
from src.api.routes import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Initialize database on startup
    from src.core.database import init_db
    init_db()
    
    # Run the application
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)