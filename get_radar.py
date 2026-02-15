#!/usr/bin/env python3
import os, requests, time
from PIL import Image

DATA_DIR = "/home/pi/allsky_guard"
CSK_ID_FILE = os.path.join(DATA_DIR, "csk_id.txt")
RADAR_FILE = os.path.join(DATA_DIR, "radar_coords.txt")
CLOCK_OUT = os.path.join(DATA_DIR, "clock.png")
RADAR_OUT = os.path.join(DATA_DIR, "radar.png")

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SumnerGuard/2.0'}

def update():
    # 1. ClearSky Sync
    if os.path.exists(CSK_ID_FILE):
        with open(CSK_ID_FILE, "r") as f:
            c_id = f.read().strip()
        if c_id:
            url = f"https://www.cleardarksky.com/c/{c_id}csk.gif?c={int(time.time())}"
            try:
                r = requests.get(url, headers=HEADERS, timeout=15)
                if r.status_code == 200:
                    with open(CLOCK_OUT + ".gif", "wb") as f: f.write(r.content)
                    with Image.open(CLOCK_OUT + ".gif") as img: img.save(CLOCK_OUT)
                    os.remove(CLOCK_OUT + ".gif")
                    print(f"Clock Updated: {c_id}")
            except: print("Clock Fetch Failed")

    # 2. Radar Sync
    if os.path.exists(RADAR_FILE):
        with open(RADAR_FILE, "r") as f:
            r_id = f.read().strip().upper()
        if r_id:
            url = f"https://radar.weather.gov/ridge/standard/{r_id}_0.gif"
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    with open(RADAR_OUT, "wb") as f: f.write(r.content)
                    print(f"Radar Updated: {r_id}")
            except: print("Radar Fetch Failed")

if __name__ == "__main__":
    update()
