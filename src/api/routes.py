"""
Flask routes for QuickCompare API.
"""

from flask import Blueprint, request, jsonify
from .handlers import ConfigHandler, SearchHandler, ETAHandler, StaticHandler

# Create Blueprint for API routes
api_bp = Blueprint('api', __name__)

# Initialize handlers
config_handler = ConfigHandler()
search_handler = SearchHandler(debug=True)
eta_handler = ETAHandler()
static_handler = StaticHandler()


@api_bp.route("/config", methods=['GET'])
def get_config():
    """Get application configuration."""
    config = config_handler.get_config()
    return jsonify(config)


@api_bp.route('/search', methods=['POST'])
def search():
    """Search for products across all platforms."""
    try:
        request_data = request.get_json()
        results, status_code = search_handler.search_products(request_data)
        return jsonify(results), status_code
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@api_bp.route('/eta', methods=['POST'])
def eta():
    """Get delivery ETA for all platforms."""
    try:
        request_data = request.get_json()
        eta_results, status_code = eta_handler.get_eta(request_data)
        return jsonify(eta_results), status_code
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


def register_static_routes(app):
    """Register static file routes with the main app."""
    
    @app.route('/')
    def home():
        """Serve the home page."""
        return app.send_static_file('index.html')
    
    return app


def create_app():
    """Application factory function."""
    from flask import Flask
    from dotenv import load_dotenv
    import os
    
    # Load environment variables
    load_dotenv()
    
    # Get the project root directory (two levels up from this file)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    static_folder = os.path.join(project_root, 'static')
    
    # Create Flask app with correct static folder path
    app = Flask(__name__, 
                static_folder=static_folder,
                static_url_path='/static')
    
    # Register API blueprint
    app.register_blueprint(api_bp)
    
    # Register static routes
    register_static_routes(app)
    
    return app
