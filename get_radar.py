#!/usr/bin/env python3
import os
import requests
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DATA_DIR = "/home/pi/allsky_guard"
COORD_FILE = os.path.join(DATA_DIR, "radar_coords.txt")
DEFAULT_RADAR_ID = "KGRR" 

CLOCKS = {
    "clock_wyoming.png": "https://www.cleardarksky.com/c/HwkHlObMIcsk.gif",
    "clock_sumner.png": "https://www.cleardarksky.com/c/CdnLkMIcsk.gif"
}

# Enhanced headers to mimic a real Chrome browser session
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive'
}

def get_radar_url():
    radar_id = DEFAULT_RADAR_ID
    if os.path.exists(COORD_FILE):
        try:
            with open(COORD_FILE, "r") as f:
                content = f.read().strip().upper()
                if content: radar_id = content
        except: pass
    
    # Updated URL format for the GIS background-integrated radar
    ts = int(time.time())
    return f"https://radar.weather.gov/ridge/standard/{radar_id}_0.gif?t={ts}"

def update_data():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    
    targets = {"radar.png": get_radar_url()}
    targets.update(CLOCKS)

    print(f"--- Syncing Allsky Guard: {datetime.now().strftime('%H:%M:%S')} ---")

    # Set up a session with retries for shaky NOAA connections
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    for filename, url in targets.items():
        try:
            # Verify SSL and use full browser headers
            r = session.get(url, headers=HEADERS, timeout=30, verify=True)
            if r.status_code == 200:
                with open(os.path.join(DATA_DIR, filename), "wb") as f:
                    f.write(r.content)
                print(f"  [SUCCESS] {filename}")
            else:
                print(f"  [ERROR {r.status_code}] {filename}")
        except Exception as e:
            print(f"  [FAILED] {filename}: {e}")

    # Log operational hours (0.25 hrs)
    hrs_file = os.path.join(DATA_DIR, "hours.txt")
    current_hrs = 0.0
    if os.path.exists(hrs_file):
        try:
            with open(hrs_file, "r") as f: 
                content = f.read().strip()
                if content: current_hrs = float(content)
        except: pass
    with open(hrs_file, "w") as f: f.write(f"{current_hrs + 0.25:.1f}")

if __name__ == "__main__":
    update_data()
