"""
Swiggy Instamart ETA fetcher
"""

from playwright.sync_api import sync_playwright
from src.core.geocoding import geocode_address
import threading

# Thread-local storage for Playwright instances
_thread_local = threading.local()

def _get_browser():
    """Get or create Playwright browser instance (thread-local)"""
    if not hasattr(_thread_local, 'playwright') or _thread_local.browser is None or not _thread_local.browser.is_connected():
        print("🚀 Starting Playwright browser for Instamart...")
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
            print(f"⚠️ Instamart: Could not geocode address '{address}'")
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
                    print(f"✓ Instamart ETA: {eta}")
                    return eta
                except (KeyError, IndexError, TypeError) as e:
                    print(f"⚠️ Instamart: Failed to parse response: {e}")
                    return "N/A"
            else:
                print(f"⚠️ Instamart API returned status {response.status}")
                return "N/A"
        
        finally:
            page.close()
    
    except Exception as e:
        print(f"⚠️ Instamart ETA error: {e}")
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
