from playwright.sync_api import sync_playwright, TimeoutError
import time, re, json

# --- tiny retry helper (blinkit-style) ---
def try_until_success(fn, retries=3, delay=0.8):
    for i in range(retries):
        try:
            return fn()
        except TimeoutError as e:
            print(f"⏳ Retry {i+1}/{retries} after: {e}")
            time.sleep(delay)
    raise TimeoutError("All retries failed")

RUPEE_RE  = re.compile(r'₹\s*([0-9][0-9,]*(?:\.\d+)?)')
PODID_RE  = re.compile(r'podId["\']?\s*[:=]\s*["\']?(\d+)["\']?', re.IGNORECASE)

# ---- Selectors ----
SEL = {
    "grid": "#bottom-hud-wrapper ._3ZzU7, ._179Mx",
    "card": 'div[data-testid="default_container_ux4"].XjYJe, #bottom-hud-wrapper ._3ZzU7 > div > div > div > div',

    "image": '._1OklP._1TqJT > img',
    "name":  '.sc-aXZVg.kyEzVU._1sPB0',
    "qty":   '.entQHA._3eIPt, [data-testid="item-quantity"] [aria-label]',
    "price_offer": '[data-testid="item-offer-price"]',
    "price_any":   '._20EAu [aria-label], ._20EAu div[aria-label]',

    "eta": '._2AY8J',
    "use_loc": 'div[data-testid="set-gps-button"]',
    "search_triggers": [
        '._1AaZg','._1wmlH',
        '[data-testid="search-trigger"]',
        'div[role="button"][aria-label*="Search"]',
        'div[class*="search"] input[readonly]',
        'div[class*="search"]',
    ],
    "real_input": 'input[placeholder*="Search"], input[type="search"]:not([readonly])',
}

def _clean_price(text: str) -> str:
    if not text:
        return "N/A"
    text = text.strip()
    if text.isdigit():
        return f"₹{text}"
    m = RUPEE_RE.search(text)
    return f"₹{m.group(1)}" if m else "N/A"

def _parse_rupee_to_float(s: str) -> float | None:
    if not s: return None
    m = RUPEE_RE.search(s)
    if not m: return None
    try:
        return float(m.group(1).replace(",", ""))
    except Exception:
        return None

def _rupee_from_number(num) -> str:
    try:
        x = float(num)
        if x > 10000:  # paise→₹ heuristic
            x = x / 100.0
        s = f"{x:.2f}".rstrip("0").rstrip(".")
        return f"₹{s}"
    except Exception:
        return "N/A"

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def _norm_qty(q: str) -> str:
    s = _norm(q)
    s = s.replace("ltr", "l")
    s = s.replace("gms", "g").replace("gm", "g")
    s = s.replace("×", "x")
    s = re.sub(r"\s*x\s*", " x ", s)
    return re.sub(r"\s+", " ", s).strip()

def _build_api_indexes(api_items: list[dict]):
    by_name_qty = {}
    by_name = {}

    def put(key, row):
        if key:
            by_name_qty[key] = row

    def put_name(nkey, row):
        if nkey and nkey not in by_name:
            by_name[nkey] = row  # first occurrence

    for o in api_items:
        pid  = str(o.get("product_id") or "").strip()
        name = (o.get("display_name") or o.get("name") or "").strip()
        qty  = (o.get("quantity") or o.get("packSize") or o.get("unit") or "").strip()
        instock = bool(o.get("in_stock") if o.get("in_stock") is not None else o.get("inStock", True))
        # best-effort numeric price
        price = (o.get("offer_price") or o.get("final_price") or o.get("price") or o.get("mrp"))
        if isinstance(price, dict):
            price = price.get("offer_price") or price.get("final_price") or price.get("price") or price.get("mrp")

        if not pid or not name:
            continue

        row = {
            "product_id": pid,
            "display_name": name,
            "quantity": qty,
            "in_stock": instock,
            "api_price": price,
        }
        key = f"{_norm(name)} | {_norm_qty(qty)}" if qty else None
        put(key, row)
        put_name(_norm(name), row)

    return by_name_qty, by_name

def _collect_api_after_search(page, timeout_ms=60000):
    """
    Actively wait for the Instamart search API response and parse it.
    Returns the harvested `items` list (flattened across payload shapes).
    """
    patterns = (
        "/api/instamart/search/mart",  # v2 variant you observed
        "/api/instamart/search",       # generic
        "/api/instamart/catalog",      # other fallback
    )

    def _predicate(resp):
        url = (resp.url or "").lower()
        return any(p in url for p in patterns)

    # give Instamart a moment to fire the request
    try:
        resp = page.wait_for_event("response", predicate=_predicate, timeout=timeout_ms)
    except TimeoutError:
        return []

    # parse JSON even if content-type is odd
    try:
        data = resp.json()
    except Exception:
        try:
            data = json.loads(resp.text() or "{}")
        except Exception:
            return []

    # flatten plausible locations of product arrays
    items = []

    def walk(o):
        if isinstance(o, dict):
            # common leaf shape
            if "product_id" in o and ("display_name" in o or "name" in o):
                items.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    return items

def run_instamart_scraper(search_query, address=None, latitude=18.502668, longitude=73.807327, headed=True):
    with sync_playwright() as p:
        UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")

        browser = p.chromium.launch(
            headless=not headed,
            args=["--no-sandbox","--disable-dev-shm-usage","--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1366, "height": 2000},
            geolocation={"latitude": latitude, "longitude": longitude},
            permissions=["geolocation"],
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        context.add_init_script('Object.defineProperty(navigator, "webdriver", { get: () => undefined });')
        page = context.new_page()

        # 1) Navigate
        print("➡️ Navigating to Instamart")
        try_until_success(lambda: page.goto("https://www.swiggy.com/instamart", timeout=60000))

        # 2) Use current location
        try:
            try_until_success(lambda: page.wait_for_selector(SEL["use_loc"], timeout=8000).click())
            print("📍 Used current location")
        except TimeoutError:
            print("⚠️ 'Use current location' not found; relying on injected geolocation")

        # Nudge geolocation
        page.evaluate(
            """({lat,lng})=>{
                const pos={coords:{latitude:lat,longitude:lng,accuracy:10},timestamp:Date.now()};
                try{navigator.geolocation.getCurrentPosition(cb=>cb(pos),()=>{})}catch(_){}
                try{navigator.geolocation.watchPosition(cb=>cb(pos),()=>{})}catch(_){}
            }""",
            {"lat": latitude, "lng": longitude},
        )
        page.wait_for_timeout(1000)

        # 3) Extract podId via full reload (view-source-like)
        pod_id = None
        try:
            resp1 = page.reload(wait_until="load")
            html = resp1.text() if resp1 else ""
            m = PODID_RE.search(html or "")
            pod_id = m.group(1) if m else None
            print("🏬 podId:", pod_id or "NOT FOUND")
        except Exception:
            print("⚠️ Could not read podId from reload")

        # 4) ETA (optional)
        delivery_time = "N/A"
        try:
            dt = page.query_selector(SEL["eta"])
            if dt:
                raw = (dt.inner_text() or "").strip().lower()
                m = re.search(r'(\d+)\s*min', raw)
                delivery_time = f"{m.group(1)} mins" if m else (raw or "N/A")
        except Exception:
            pass
        print(f"⏳ Delivery time (header): {delivery_time}")

        # 5) Open the real search input and submit the query
        try:
            def click_trigger():
                for sel in SEL["search_triggers"]:
                    loc = page.locator(sel).first
                    if loc.count():
                        loc.click(timeout=1200, force=True)
                        return True
                page.mouse.click(300, 120)
                return True
            try_until_success(click_trigger, retries=3, delay=0.5)

            def get_real_input():
                locator = page.locator(SEL["real_input"])
                locator.wait_for(state="visible", timeout=15000)
                for h in locator.element_handles():
                    if h.get_attribute("readonly") is None:
                        return h
                raise TimeoutError("Only readonly inputs found")
            real_input = try_until_success(get_real_input, retries=3, delay=0.6)

            real_input.click()
            page.keyboard.down("Control"); page.keyboard.press("A"); page.keyboard.up("Control")
            page.keyboard.press("Backspace")
            page.keyboard.type(search_query, delay=25)
            page.keyboard.press("Enter")
            print(f"🔎 Submitted search: {search_query}")
        except TimeoutError:
            print("❌ Search bar interaction failed")
            browser.close()
            return []

        # 6) Actively capture the Instamart search API payload
        api_items = _collect_api_after_search(page, timeout_ms=60000)
        print(f"🔗 API items harvested: {len(api_items)}")
        by_name_qty, by_name = _build_api_indexes(api_items)

        # 7) Wait for grid, then scroll a bit to load more (also lets more cards render)
        try:
            try_until_success(lambda: page.wait_for_selector(SEL["grid"], state="visible", timeout=45000))
        except TimeoutError:
            print("⚠️ Results grid did not appear")
            browser.close()
            return []

        for _ in range(5):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(700)

        # 8) Parse cards and JOIN with API
        cards = page.query_selector_all(SEL["card"])
        print(f"🧩 Found {len(cards)} candidate cards")
        results = []

        for c in cards:
            try:
                img_el = c.query_selector(SEL["image"])
                image_url = img_el.get_attribute("src") if img_el else ""

                name_el = c.query_selector(SEL["name"])
                name = (name_el.inner_text().strip() if name_el else "")

                qty_el = c.query_selector(SEL["qty"])
                if qty_el:
                    quantity = (qty_el.get_attribute("aria-label") or qty_el.inner_text() or "").strip()
                else:
                    quantity = "N/A"

                price = "N/A"
                p_offer = c.query_selector(SEL["price_offer"])
                if p_offer:
                    price = _clean_price(p_offer.get_attribute("aria-label") or p_offer.inner_text())
                else:
                    p_any = c.query_selector(SEL["price_any"])
                    if p_any:
                        price = _clean_price(p_any.get_attribute("aria-label") or p_any.inner_text())

                # --- JOIN: key, fallback name-only, fallback price proximity
                norm_key = f"{_norm(name)} | {_norm_qty(quantity)}"
                api_row = by_name_qty.get(norm_key)

                if not api_row:
                    api_row = by_name.get(_norm(name))

                if not api_row and by_name:
                    # price proximity fallback
                    dom_price = _parse_rupee_to_float(price)
                    if dom_price is not None:
                        best, best_delta = None, 1e9
                        for row in by_name.values():
                            rv = row.get("api_price")
                            if rv in (None, "", "None"): 
                                continue
                            try:
                                cand = float(rv)
                                if cand > 10000: cand /= 100.0
                                delta = abs(cand - dom_price)
                                if delta < best_delta:
                                    best, best_delta = row, delta
                            except Exception:
                                pass
                        api_row = best

                product_id = (api_row or {}).get("product_id", "")
                in_stock   = (api_row or {}).get("in_stock", True)
                api_price_val = (api_row or {}).get("api_price", None)
                if api_price_val not in (None, "", "None"):
                    price = _rupee_from_number(api_price_val) or price or "N/A"

                product_url = (f"https://www.swiggy.com/instamart/item/{product_id}?storeId={pod_id}"
                               if product_id and pod_id else page.url)

                results.append({
                    "platform": "instamart",
                    "name": name,
                    "price": price,
                    "quantity": quantity,
                    "image_url": image_url,
                    "product_url": product_url,
                    "delivery_time": delivery_time,
                    "in_stock": in_stock,
                    "product_id": product_id,
                })
            except Exception as e:
                print(f"⚠️ Card parse error: {e}")
                continue

        print(f"✅ Scraped {len(results)} items (API matched: {sum(1 for r in results if r.get('product_id'))})")
        browser.close()
        return results

# required for app.py import
def product_key(item):
    return item.get("product_url")

def is_complete(item):
    return all([item.get("name"), item.get("price"), item.get("product_url")])

# --- Manual test ---
if __name__ == "__main__":
    out = run_instamart_scraper(
        "amul milk",
        "Kothrud, Pune 411038",
        latitude=18.502668,
        longitude=73.807327,
        headed=True
    )
    from pprint import pprint
    pprint(out[:10]); print("Total:", len(out))
