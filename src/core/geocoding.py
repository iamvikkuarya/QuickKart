"""Geocoding helper using Google Maps API"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

geocoding_cache = {}

def geocode_address(address):
    """Convert address to lat/lng using Google Maps Geocoding API"""
    if not address:
        return None, None
    
    cache_key = address.strip().lower()
    if cache_key in geocoding_cache:
        return geocoding_cache[cache_key]
    
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("⚠️ GOOGLE_MAPS_API_KEY not found")
        return None, None
    
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": api_key, "region": "in"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "OK" and data.get("results"):
                location = data["results"][0]["geometry"]["location"]
                lat, lng = location["lat"], location["lng"]
                geocoding_cache[cache_key] = (lat, lng)
                return lat, lng
    except Exception as e:
        print(f"⚠️ Geocoding error: {e}")
    
    return None, None
