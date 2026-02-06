#!/bin/bash
echo "--- Sumner Guard: Full System Installation ---"

# 1. Update and Install System Dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-tk git smbus2 raspi-config

# 2. Install Python Libraries (Required for Pi 5)
pip3 install Pillow requests smbus2 RPi.bme280 RPi.GPIO --break-system-packages

# 3. Create Folder Structure
mkdir -p /home/pi/allsky_guard
mkdir -p /home/pi/.config/autostart

# 4. Deploy Files
cp *.py /home/pi/allsky_guard/
cp hud.desktop /home/pi/.config/autostart/
chmod +x /home/pi/allsky_guard/*.py

# 5. Initialize Data Files
if [ ! -f /home/pi/allsky_guard/hours.txt ]; then
    echo "0.0" > /home/pi/allsky_guard/hours.txt
fi
touch /home/pi/allsky_guard/sensors.txt

# 6. Enable I2C (Required for BME280/MLX)
sudo raspi-config nonint do_i2c 0

# 7. Setup Systemd Services (Sync & Sensors)
if [ -f sumner_sync.timer ]; then
    sudo cp sumner_sync.* /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now sumner_sync.timer
fi

echo "--- Installation Complete! Please Reboot ---"
