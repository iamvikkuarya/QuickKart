# eta_dmart.py
import requests

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.dmart.in",
    "Referer": "https://www.dmart.in/",
}

def get_unique_id(search_text: str) -> str:
    """Fetch uniqueId for a given pincode/address."""
    url = "https://digital.dmart.in/api/v2/pincodes/suggestions"
    resp = requests.post(url, json={"searchText": search_text}, headers=BASE_HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("searchResult", [])
    return results[0]["uniqueId"] if results else ""

def get_store_id(pincode: str, unique_id: str) -> str:
    """Fetch storeId using uniqueId + pincode."""
    url = "https://digital.dmart.in/api/v2/pincodes/details"
    payload = {
        "uniqueId": unique_id,
        "apiMode": "GA",
        "pincode": pincode,
        "currentLat": "",
        "currentLng": "",
    }
    resp = requests.post(url, json=payload, headers=BASE_HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return str(data.get("storePincodeDetails", {}).get("storeId", ""))

def get_dmart_eta(pincode_or_address: str) -> str:
    """Fetch ETA/delivery slot for Dmart using pincode/address."""
    try:
        unique_id = get_unique_id(pincode_or_address)
        if not unique_id:
            return "N/A"

        store_id = get_store_id(pincode_or_address, unique_id)
        if not store_id:
            return "N/A"

        url = f"https://digital.dmart.in/api/v2/pincodes/earliestslot/{pincode_or_address}?storeId={store_id}"
        resp = requests.get(url, headers=BASE_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        slots = data.get("slots", [])
        if not slots:
            return "N/A"

        # pick first available slot
        if "timeSlot" in slots[0]:
            return slots[0]["timeSlot"]

        if slots[0].get("type") == "PUP" and slots[0].get("PUPData"):
            return slots[0]["PUPData"][0].get("timeSlot", "N/A")

        return "N/A"
    except Exception as e:
        print("⚠️ ETA fetch failed:", e)
        return "N/A"

if __name__ == "__main__":
    # Works with pincode or address string
    print("ETA:", get_dmart_eta("411038"))