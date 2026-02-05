#!/usr/bin/env python3
import requests
from PIL import Image
import os

CHARTS = {
    "Wyoming": "GraRapKMI",
    "Sumner": "MSUObMI"
}
PATH = "/home/pi/allsky_guard/"

def update_charts():
    for name, chart_id in CHARTS.items():
        url = f"https://www.cleardarksky.com/c/{chart_id}csk.gif"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                # Save temp gif
                temp_gif = f"{PATH}{name}_temp.gif"
                with open(temp_gif, 'wb') as f:
                    f.write(r.content)
                
                # Convert to PNG for Tkinter compatibility
                img = Image.open(temp_gif)
                img.save(f"{PATH}{name}_forecast.png")
                print(f"Forecast updated: {name}")
        except:
            print(f"Failed to update {name} forecast")

if __name__ == "__main__":
    update_charts()
