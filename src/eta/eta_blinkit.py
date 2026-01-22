"""
Blinkit ETA - Direct API Implementation
Uses cloudscraper to bypass Cloudflare protection
~0.5-1s response time (3-4x faster than Playwright)
"""

import cloudscraper
import time
import logging
import os
import uuid

logger = logging.getLogger(__name__)


def get_blinkit_eta(address: str, lat: str = None, lon: str = None) -> str:
    """
    Get Blinkit ETA using direct API call
    
    Args:
        address: Address string (currently not used for geocoding)
        lat: Latitude (optional, defaults to Delhi)
        lon: Longitude (optional, defaults to Delhi)
    
    Returns:
        ETA string like "15 min" or "N/A"
    
    Performance: ~0.5-1 second
    """
    
    # Default coordinates from env or fallback to Delhi
    use_lat = lat or os.getenv('BLINKIT_DEFAULT_LAT', '28.4652382')
    use_lon = lon or os.getenv('BLINKIT_DEFAULT_LON', '77.0615957')
    
    try:
        start_time = time.time()
        
        # Create cloudscraper session (bypasses Cloudflare)
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        # Blinkit ETA API endpoint
        url = "https://blinkit.com/v1/consumerweb/eta"
        
        # Headers - using env vars for configurability
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://blinkit.com',
            'Referer': 'https://blinkit.com/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'app_client': 'consumer_web',
            'platform': 'desktop_web',
            'web_app_version': os.getenv('BLINKIT_WEB_APP_VERSION', '1008010016'),
            'app_version': os.getenv('BLINKIT_APP_VERSION', '52434332'),
            'x-age-consent-granted': 'false',
            'access_token': 'null',
            'lat': use_lat,
            'lon': use_lon,
            'device_id': str(uuid.uuid4())[:16],
            'session_uuid': str(uuid.uuid4()),
        }
        
        # Make API call
        response = scraper.get(url, headers=headers, timeout=10)
        
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            eta_minutes = data.get('eta_in_minutes')
            
            if eta_minutes and str(eta_minutes).isdigit():
                logger.debug(f"Blinkit ETA: {eta_minutes} min (took {duration:.2f}s)")
                return f"{eta_minutes} min"
            else:
                logger.info(f"Blinkit store unavailable at this location")
                return "Store Unavailable"
        else:
            logger.warning(f"Blinkit ETA API returned status {response.status_code}")
            return "N/A"
            
    except Exception as e:
        logger.error(f"Blinkit ETA error: {e}")
        return "N/A"


if __name__ == "__main__":
    print("Blinkit ETA:", get_blinkit_eta("Azad Nagar, Kothrud"))
