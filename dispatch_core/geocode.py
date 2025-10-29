import os
import time
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = os.getenv("GEOCODER_UA", "taxi-dispatch-cw/1.0 (student project)")

def geocode(address: str):
    if not address:
        return None, None
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": USER_AGENT}
    # маленький таймаут и антиспам-пауза на всякий
    resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=5)
    time.sleep(1.0)
    if resp.status_code != 200:
        return None, None
    data = resp.json()
    if not data:
        return None, None
    return float(data[0]["lat"]), float(data[0]["lon"])