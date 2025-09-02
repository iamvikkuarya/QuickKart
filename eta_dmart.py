# eta_dmart.py
from playwright.sync_api import sync_playwright

def get_dmart_eta(pincode: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # keep False for debugging
        context = browser.new_context()
        page = context.new_page()

        context.route("**/*", lambda route: (
            route.abort() if route.request.resource_type in ["image", "font", "stylesheet"] else route.continue_()
        ))

        # 1. Open homepage
        page.goto("https://www.dmart.in/", timeout=60000)

        # 2. Fill the pincode input
        page.wait_for_selector("#pincodeInput", timeout=15000)
        page.fill("#pincodeInput", pincode)

        # 3. Wait for suggestions and click first
        first_suggestion = (
            "body > div.MuiDialog-root.pincode-widget_container__9Ru5k "
            "> div.MuiDialog-container > div > div > div "
            "> div.pincode-widget_pincode-body__g684i ul > li:nth-child(1) > button"
        )
        page.wait_for_selector(first_suggestion, timeout=8000)
        page.eval_on_selector(first_suggestion, "el => el.click()")

        # 4. Confirm location
        page.wait_for_selector("button:has-text('CONFIRM LOCATION')", timeout=10000)
        page.click("button:has-text('CONFIRM LOCATION')", force=True)

        # 5. Wait for page to reload with header ETA
        page.wait_for_timeout(1000)

        # 6. Grab ETA from header
        eta_selector = (
            "#__next > div.layout_container__GDOMj > header > div > "
            "div.header_header-container__HCWdL > div.header_logo-container__vCOK2 > div > "
            "div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-md-5.header_sepBorder__eD530.mui-style-1r482s6 " #this one works
            "> div:nth-child(2) > div:nth-child(2)"
        )

        eta_text = ""
        try:
            page.wait_for_selector(eta_selector, timeout=2000)
            eta_text = page.text_content(eta_selector).strip()
        except Exception as e:
            print(f"⚠️ ETA not found: {e}")
            eta_text = "N/A"

        browser.close()
        return eta_text

if __name__ == "__main__":
    print("ETA:", get_dmart_eta("Azad Nagar Kothrud"))
