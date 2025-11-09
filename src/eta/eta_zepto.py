# eta_zepto.py
from playwright.sync_api import sync_playwright
import re, random

# Enhanced user agents for better stealth
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

UA = random.choice(USER_AGENTS)  # Maintain compatibility with existing code

def normalize_eta(raw: str) -> str:
    """Extract minutes and return clean 'X min' format."""
    if not raw:
        return "N/A"
    
    raw = raw.strip().lower()
    
    # Enhanced patterns for better ETA extraction
    patterns = [
        r'(\d+)\s*min(?:ute)?s?',           # "10 mins", "15 minutes"
        r'in\s*(\d+)\s*min',                # "in 10 min"
        r'delivery\s*in\s*(\d+)',           # "delivery in 15"
        r'(\d+)\s*-\s*(\d+)\s*min',         # "10-15 min" - take first number
        r'within\s*(\d+)',                  # "within 20"
        r'(\d+)',                           # any number as fallback
    ]
    
    for pattern in patterns:
        match = re.search(pattern, raw)
        if match:
            minutes = match.group(1)
            return f"{minutes} min"
    
    # Check for unavailable indicators
    unavailable_indicators = [
        'unavailable', 'closed', 'not available', 'no delivery',
        'out of service', 'temporarily closed'
    ]
    
    if any(indicator in raw for indicator in unavailable_indicators):
        return "Store Unavailable / Closed"
    
    return "N/A"


def get_zepto_eta(address: str, headed: bool = False) -> str:
    """
    Fetch delivery ETA for Zepto.
    Requires a valid address string (validated upstream in app.py).
    """
    with sync_playwright() as p:
        # Enhanced browser launch with optimizations
        browser = p.chromium.launch(
            headless=not headed,
            args=[
                "--no-sandbox", 
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run"
            ]
        )
        
        # Enhanced context with better stealth
        context = browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            extra_http_headers={
                "Accept-Language": "en-IN,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br"
            }
        )
        page = context.new_page()
        eta = "N/A"

        # Enhanced resource blocking for speed
        context.route("**/*", lambda route: (
            route.abort() if route.request.resource_type in ["image", "font", "media"] 
            else route.continue_()
        ))
        
        # Enhanced stealth
        context.add_init_script('Object.defineProperty(navigator, "webdriver", { get: () => undefined });')

        try:
            # Optimized navigation with reduced timeout
            page.goto("https://www.zeptonow.com/", timeout=25000)

            # Enhanced location setting with multiple fallbacks
            location_set = False
            
            # Try location button click with reduced timeout
            try:
                page.click('button[aria-label="Select Location"]', timeout=8000)
                location_set = True
            except:
                # Fallback: try other location selectors
                location_selectors = [
                    '[data-testid="location-button"]',
                    'button:has-text("Select Location")'
                ]
                for selector in location_selectors:
                    try:
                        page.click(selector, timeout=5000)
                        location_set = True
                        break
                    except:
                        continue
            
            if not location_set:
                return "Location Setup Failed"
            
            # Enhanced address input with multiple fallbacks
            input_filled = False
            input_selectors = [
                'div[data-testid="address-search-input"] input',
                'input[placeholder*="Search"]',
                'input[type="text"]',
                'input[placeholder*="address"]'
            ]
            
            for selector in input_selectors:
                try:
                    page.fill(selector, address, timeout=3000)
                    page.wait_for_timeout(800)
                    input_filled = True
                    break
                except:
                    continue
            
            if not input_filled:
                return "Address Input Failed"
            
            # Enhanced suggestion click with multiple fallbacks
            suggestion_clicked = False
            suggestion_selectors = [
                'div[data-testid="address-search-item"]',
                '[role="option"]',
                '.suggestion-item',
                'li:has-text("' + address.split(',')[0] + '")'
            ]
            
            for selector in suggestion_selectors:
                try:
                    page.click(selector, timeout=5000)
                    suggestion_clicked = True
                    break
                except:
                    continue
            
            if not suggestion_clicked:
                # Final fallback: press Enter
                page.keyboard.press("Enter")
                page.wait_for_timeout(1500)
            
            # Enhanced location confirmation with fallback
            try:
                page.click('button[data-testid="location-confirm-btn"]', timeout=8000)
            except:
                # Sometimes location is auto-confirmed
                pass
            
            # Optimized wait and scroll
            page.wait_for_timeout(1500)  # Reduced from 800
            page.evaluate("window.scrollBy(0,200)")  # Reduced scroll
            page.wait_for_timeout(500)

            # Enhanced ETA extraction with more selectors
            raw = ""
            eta_selectors = [
                "[data-testid='delivery-time']",
                "span.font-extrabold",
                "[data-testid*='eta']",
                "[data-testid*='delivery']",
                ".delivery-time",
                "span:has-text('min')",
                "*:has-text('delivery in')",
                ":text('min')",
            ]
            
            for sel in eta_selectors:
                try:
                    el = page.locator(sel).first
                    if el.count():
                        text = el.inner_text().strip()
                        if text and ('min' in text.lower() or any(char.isdigit() for char in text)):
                            raw = text
                            break
                except:
                    continue
            
            # Fallback: scan page text for ETA patterns
            if not raw:
                try:
                    page_text = page.inner_text("body")
                    eta_patterns = [
                        r'delivery in (\d+(?:-\d+)?) min',
                        r'(\d+) min delivery',
                        r'delivered in (\d+) min'
                    ]
                    
                    for pattern in eta_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            raw = match.group(0)
                            break
                except:
                    pass
            
            eta = normalize_eta(raw)

        except Exception as e:
            # Enhanced error handling
            eta = "Error"
            
        finally:
            browser.close()
        return eta


if __name__ == "__main__":
    # Example: must pass explicit address
    print("Zepto ETA:", get_zepto_eta("Azad Nagar, Pune"))