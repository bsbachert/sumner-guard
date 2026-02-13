#!/bin/bash
echo "--- Sumner Guard: Full System Installation & Update ---"

# 1. Update and Install System Dependencies
# Added 'gio-bin' for app launching and 'libatlas-base-dev' for numerical math
sudo apt-get update
sudo apt-get install -y python3-pip python3-tk git smbus2 raspi-config gio-bin libatlas-base-dev

# 2. Install Python Libraries (Required for Pi 5 & New Radar Logic)
# geopy added for zip-to-coordinates conversion
pip3 install Pillow requests smbus2 RPi.bme280 RPi.GPIO geopy --break-system-packages

# 3. Create Folder Structure
mkdir -p /home/pi/allsky_guard
mkdir -p /home/pi/.config/autostart

# 4. Deploy Files
# Ensures the Python script and autostart entry are moved to correct locations
cp *.py /home/pi/allsky_guard/
cp hud.desktop /home/pi/.config/autostart/
chmod +x /home/pi/allsky_guard/*.py

# 5. Initialize/Preserve Data Files
# Using [ ! -f ] checks to ensure we don't overwrite your existing data during an update
[ ! -f /home/pi/allsky_guard/hours.txt ] && echo "0.0" > /home/pi/allsky_guard/hours.txt
[ ! -f /home/pi/allsky_guard/cloud_threshold.txt ] && echo "30.0" > /home/pi/allsky_guard/cloud_threshold.txt
[ ! -f /home/pi/allsky_guard/dossier.txt ] && echo "System Notes:" > /home/pi/allsky_guard/dossier.txt
[ ! -f /home/pi/allsky_guard/zipcode.txt ] && echo "10001" > /home/pi/allsky_guard/zipcode.txt
touch /home/pi/allsky_guard/sensors.txt

# 6. Enable I2C (Required for BME280/MLX sensor communication)
sudo raspi-config nonint do_i2c 0

# 7. Setup Systemd Services (Sync & Sensors)
if [ -f sumner_sync.timer ]; then
    sudo cp sumner_sync.* /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now sumner_sync.timer
fi

# 8. Setup Desktop Shortcut
# This creates the clickable icon on the desktop and marks it as "trusted" by the OS
cat <<EOF > /home/pi/Desktop/SumnerHUD.desktop
[Desktop Entry]
Type=Application
Name=Sumner HUD
Comment=Observatory Control Panel
Exec=python3 /home/pi/allsky_guard/hud.py
Icon=utilities-terminal
Terminal=false
Categories=Utility;
EOF

chmod +x /home/pi/Desktop/SumnerHUD.desktop
gio set /home/pi/Desktop/SumnerHUD.desktop metadata::trusted true

# 9. Set Permissions for Data Writing
chmod 666 /home/pi/allsky_guard/*.txt

echo "--- Installation Complete! ---"
echo "--- Please Reboot to activate I2C and Autostart. ---"