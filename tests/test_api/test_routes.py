"""
Tests for API routes functionality.
"""

import sys
import os
import pytest
import json

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.api.routes import create_app


class TestAPIRoutes:
    """Test cases for API routes."""
    
    @pytest.fixture
    def app(self):
        """Create test app fixture."""
        app = create_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture 
    def client(self, app):
        """Create test client fixture."""
        return app.test_client()
    
    def test_config_endpoint(self, client):
        """Test /config endpoint."""
        response = client.get('/config')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'maps_api_key' in data
    
    def test_home_endpoint(self, client):
        """Test home endpoint."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_search_endpoint_no_query(self, client):
        """Test /search endpoint without query."""
        response = client.post('/search', 
                             json={},
                             content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'Missing query' in data['error']
    
    def test_search_endpoint_with_query(self, client):
        """Test /search endpoint with query."""
        response = client.post('/search',
                             json={'query': 'test'},
                             content_type='application/json')
        
        # Should return 200 (even if no results)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
    
    def test_eta_endpoint(self, client):
        """Test /eta endpoint."""
        response = client.post('/eta',
                             json={'address': 'Test Address'},
                             content_type='application/json')
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'blinkit' in data
        assert 'zepto' in data
        assert 'dmart' in data


def test_basic_imports():
    """Test that all imports work correctly."""
    from src.api.routes import api_bp, create_app
    from src.api.handlers import ConfigHandler, SearchHandler, ETAHandler
    
    # Should not raise exceptions
    app = create_app()
    assert app is not None
    
    config_handler = ConfigHandler()
    assert config_handler is not None


if __name__ == "__main__":
    # Run basic import test
    try:
        test_basic_imports()
        print("✅ Import test passed")
        
        # Test app creation
        app = create_app()
        client = app.test_client()
        
        # Test config endpoint
        response = client.get('/config')
        if response.status_code == 200:
            print("✅ Config endpoint test passed")
        else:
            print(f"❌ Config endpoint test failed: {response.status_code}")
        
        print("🎉 Basic API tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)