#!/usr/bin/env python3
import os
import requests
from datetime import datetime

DATA_DIR = "/home/pi/allsky_guard"
COORD_FILE = os.path.join(DATA_DIR, "radar_coords.txt")

# Default if file doesn't exist (KGRR - Wyoming/Grand Rapids area)
DEFAULT_RADAR_ID = "KGRR" 

CLOCKS = {
    "clock_wyoming.png": "https://www.cleardarksky.com/c/HwkHlObMIcsk.gif",
    "clock_sumner.png": "https://www.cleardarksky.com/c/CdnLkMIcsk.gif"
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Referer': 'https://www.cleardarksky.com/'
}

def get_radar_url():
    # NOAA uses Station IDs (KGRR, KLWX, etc). 
    # If you prefer Lat/Long, specialized APIs are needed, 
    # but NOAA Station IDs are free and high-res.
    radar_id = DEFAULT_RADAR_ID
    if os.path.exists(COORD_FILE):
        with open(COORD_FILE, "r") as f:
            radar_id = f.read().strip().upper()
    return f"https://radar.weather.gov/ridge/standard/{radar_id}_loop.gif"

def update_data():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    targets = {"radar.png": get_radar_url()}
    targets.update(CLOCKS)

    print(f"--- Syncing Allsky Guard: {datetime.now().strftime('%H:%M:%S')} ---")

    for filename, url in targets.items():
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                with open(os.path.join(DATA_DIR, filename), "wb") as f:
                    f.write(r.content)
                print(f"  [SUCCESS] {filename}")
            else:
                print(f"  [ERROR {r.status_code}] {filename}")
        except Exception as e:
            print(f"  [FAILED] {filename}: {e}")

    # Log operational hours
    hrs_file = os.path.join(DATA_DIR, "hours.txt")
    current_hrs = 0.0
    if os.path.exists(hrs_file):
        with open(hrs_file, "r") as f:
            try: current_hrs = float(f.read().strip())
            except: pass
    with open(hrs_file, "w") as f:
        f.write(f"{current_hrs + 0.1:.1f}")

if __name__ == "__main__":
    update_data()
