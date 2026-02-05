#!/bin/bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-tk

# Install python requirements
pip3 install -r requirements.txt

# Create directories
mkdir -p /home/pi/allsky_guard
mkdir -p /home/pi/.config/autostart

# Move files (assuming you run this from the git folder)
cp hud.py /home/pi/allsky_guard/
cp get_radar.py /home/pi/allsky_guard/
cp hud.desktop /home/pi/.config/autostart/

# Initialize hours.txt if it doesn't exist
if [ ! -f /home/pi/allsky_guard/hours.txt ]; then
    echo "0.0" > /home/pi/allsky_guard/hours.txt
fi

# Set up systemd timers (use the commands from our previous step)
# ... [Timer setup commands go here] ...