#!/bin/bash
echo "--- Sumner Guard: Custom Location & Sensor Installer ---"

# 1. Base Setup
sudo apt-get update
sudo apt-get install -y python3-pip python3-tk git smbus2 raspi-config gio-bin adb

# 2. Location Setup
read -p "Enter Zip Code for ClearDarkSky Clock: " user_zip
mkdir -p /home/pi/allsky_guard
echo "$user_zip" > /home/pi/allsky_guard/zipcode.txt

# 3. Interactive Sensor Selection
read -p "Install BME280? (y/n): " use_bme
read -p "Install MLX90614? (y/n): " use_mlx
read -p "Install Anemometer? (y/n): " use_wind

# 4. Install only what's needed
pip3 install Pillow requests geopy gspread oauth2client --break-system-packages
[[ $use_bme == "y" ]] && pip3 install RPi.bme280 --break-system-packages
[[ $use_wind == "y" ]] && pip3 install RPi.GPIO --break-system-packages

# 5. Deploy & Prune HUD UI
cp hud.py get_radar.py wind_logger.py /home/pi/allsky_guard/
[[ $use_bme == "n" ]] && sed -i '/val_amb/d; /val_hum/d; /val_pres/d' /home/pi/allsky_guard/hud.py
[[ $use_mlx == "n" ]] && sed -i '/val_sky/d; /val_cloud/d' /home/pi/allsky_guard/hud.py
[[ $use_wind == "n" ]] && sed -i '/val_wind/d' /home/pi/allsky_guard/hud.py

chmod +x /home/pi/allsky_guard/*.py
echo "--- Installation Complete! ---"
