# dmart_location.py
import requests

# --- Shared headers for all Dmart API calls ---
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


def get_unique_id(pincode: str) -> str:
    """Step 1: Get uniqueId for a given pincode."""
    url = "https://digital.dmart.in/api/v2/pincodes/suggestions"
    resp = requests.post(url, json={"searchText": pincode}, headers=BASE_HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    results = data.get("searchResult", [])
    return results[0]["uniqueId"] if results else ""


def get_store_id(pincode: str, unique_id: str) -> str:
    """Step 2: Get storeId using uniqueId + pincode."""
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


def get_store_details(pincode: str):
    """
    Main function: resolve pincode → (uniqueId, storeId).
    Returns (unique_id, store_id) or ("", "") if not found.
    """
    unique_id = get_unique_id(pincode)
    if not unique_id:
        return "", ""

    store_id = get_store_id(pincode, unique_id)
    return unique_id, store_id


if __name__ == "__main__":
    # 🔎 Quick test
    pin = "411038"
    uid, sid = get_store_details(pin)
    print(f"✅ For pincode {pin}: uniqueId={uid}, storeId={sid}")
