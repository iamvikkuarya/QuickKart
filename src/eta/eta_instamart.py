"""
Swiggy Instamart ETA fetcher
"""

from playwright.sync_api import sync_playwright
import threading
import logging

logger = logging.getLogger(__name__)

# Import geocoding - handle both direct run and module import
try:
    from src.core.geocoding import geocode_address
except ImportError:
    # When running directly, add project root to path
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.core.geocoding import geocode_address

# Thread-local storage for Playwright instances
_thread_local = threading.local()

def _get_browser():
    """Get or create Playwright browser instance (thread-local)"""
    if not hasattr(_thread_local, 'playwright') or _thread_local.browser is None or not _thread_local.browser.is_connected():
        logger.debug("Starting Playwright browser for Instamart...")
        _thread_local.playwright = sync_playwright().start()
        _thread_local.browser = _thread_local.playwright.chromium.launch(headless=True)
        _thread_local.context = _thread_local.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={'width': 1366, 'height': 768},
            locale="en-IN",
            timezone_id="Asia/Kolkata"
        )
        _thread_local.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)
    
    return _thread_local.context

def get_instamart_eta(address):
    """
    Get delivery ETA from Swiggy Instamart
    
    Args:
        address: Full address string
    
    Returns:
        str: ETA string (e.g., "10 mins") or "N/A" if failed
    """
    try:
        # Geocode address to lat/lng
        lat, lng = geocode_address(address)
        
        if lat is None or lng is None:
            logger.info(f"Instamart: Could not geocode address '{address}'")
            return "N/A"
        
        # Get browser context
        context = _get_browser()
        page = context.new_page()
        
        try:
            # Call Swiggy Instamart select-location API
            response = page.request.post(
                "https://www.swiggy.com/api/instamart/home/select-location/v2",
                data={
                    "data": {
                        "lat": lat,
                        "lng": lng,
                        "address": "",
                        "addressId": "",
                        "annotation": "",
                        "clientId": "INSTAMART-APP"
                    }
                },
                timeout=15000
            )
            
            if response.ok:
                data = response.json()
                
                # Extract delivery time from response
                try:
                    configs = data['data']['configs']['IM_PAGE_CONFIGS']['configInfo'][0]['card']
                    pod_details = configs['podDetailsList'][0]
                    sla = pod_details['serviceabilityDetails']['sla']
                    
                    delivery_minutes = int(sla['value'])
                    
                    # Format as "X min" to match other platforms
                    eta = f"{delivery_minutes} min"
                    logger.debug(f"Instamart ETA: {eta}")
                    return eta
                except (KeyError, IndexError, TypeError) as e:
                    logger.warning(f"Instamart: Failed to parse response: {e}")
                    return "N/A"
            else:
                logger.warning(f"Instamart API returned status {response.status}")
                return "N/A"
        
        finally:
            page.close()
    
    except Exception as e:
        logger.error(f"Instamart ETA error: {e}")
        return "N/A"

def cleanup():
    """Cleanup Playwright resources (call on app shutdown)"""
    if hasattr(_thread_local, 'browser') and _thread_local.browser:
        _thread_local.browser.close()
        _thread_local.browser = None
    
    if hasattr(_thread_local, 'playwright') and _thread_local.playwright:
        _thread_local.playwright.stop()
        _thread_local.playwright = None
    
    if hasattr(_thread_local, 'context'):
        _thread_local.context = None


# Test snippet
if __name__ == "__main__":
    import sys
    import os
    import time
    
    # Add project root to Python path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    # Get address from command line or use default
    address = sys.argv[1] if len(sys.argv) > 1 else "Viman Nagar, Pune"
    
    print(f"\n⏱️  Testing Instamart ETA")
    print(f"   Address: {address}")
    print("="*50)
    
    start_time = time.time()
    
    try:
        eta = get_instamart_eta(address)
        elapsed = time.time() - start_time
        
        print(f"\n✅ RESULT:")
        print(f"   ETA: {eta}")
        print(f"   Time taken: {elapsed:.2f}s")
        
        if eta != "N/A":
            print(f"   Status: ✅ Success")
        else:
            print(f"   Status: ❌ Failed to get ETA")
    
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ ERROR after {elapsed:.2f}s:")
        print(f"   {str(e)}")
    
    finally:
        cleanup()
        print(f"\n🧹 Cleanup completed")
    
    # Test multiple addresses
    if len(sys.argv) == 1:  # Only if no custom address provided
        print(f"\n🔄 Testing multiple addresses...")
        test_addresses = [
            "Koregaon Park, Pune",
            "Baner, Pune", 
            "Whitefield, Bangalore"
        ]
        
        for addr in test_addresses:
            print(f"\n📍 Testing: {addr}")
            start_time = time.time()
            eta = get_instamart_eta(addr)
            elapsed = time.time() - start_time
            print(f"   ETA: {eta} ({elapsed:.2f}s)")
        
        cleanup()
