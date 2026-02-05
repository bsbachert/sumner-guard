#!/usr/bin/env python3
import os, time, smbus2, bme280
import RPi.GPIO as GPIO
from mlx90614 import MLX90614

# --- CONFIG ---
DATA_DIR = "/home/pi/allsky_guard"
SENSOR_FILE = os.path.join(DATA_DIR, "sensors.txt")
HOURS_FILE = os.path.join(DATA_DIR, "hours.txt")
RAIN_PIN = 22
WIND_PIN = 4
HAS_WIND = False  # Keep False until anemometer is wired up

# --- GPIO SETUP ---
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(RAIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- I2C SETUP ---
bus = smbus2.SMBus(1)
mlx = MLX90614(bus, address=0x5a)
bme_params = bme280.load_calibration_params(bus, 0x76)

def get_live_data():
    try:
        # 1. Read BME280 (Air)
        b_sample = bme280.sample(bus, 0x76, bme_params)
        air_f = (b_sample.temperature * 9/5) + 32
        
        # 2. Read MLX90614 (Sky)
        sky_f = (mlx.get_obj_temp() * 9/5) + 32
        
        # 3. Rain Status
        rain_status = "⚠️ WET" if GPIO.input(RAIN_PIN) == GPIO.LOW else "☀️ DRY"

        # 4. 1,000 Hour Logic
        if not os.path.exists(HOURS_FILE):
            with open(HOURS_FILE, "w") as f: f.write("0.0")
        with open(HOURS_FILE, "r+") as f:
            h = float(f.read().strip() or 0) + (2/3600) 
            f.seek(0); f.write(f"{h:.4f}"); f.truncate()
            maint = " !!! CLEANING DUE !!!" if h >= 1000 else ""

        # 5. Build HUD Data
        return (f"--- SUMNER GUARD DATA ---\n"
                f"SKY STATE:  LIVE\n"
                f"WIND SPEED: 0.0 MPH\n"
                f"PRECIP:     {rain_status}\n"
                f"AMB TEMP:   {air_f:.1f}°F\n"
                f"HUMIDITY:   {b_sample.humidity:.1f}%\n"
                f"IR SKY:     {sky_f:.1f}°F\n"
                f"-------------------------\n"
                f"LAST SYNC:  {time.strftime('%H:%M:%S')}{maint}")
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == "__main__":
    print("Starting Sumner Guard Master Script...")
    while True:
        output = get_live_data()
        with open(SENSOR_FILE, "w") as f:
            f.write(output)
        time.sleep(2)
