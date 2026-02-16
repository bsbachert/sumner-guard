=====================================================
    SUMNER GUARD: INSTALLATION GUIDE
=====================================================

1. SOFTWARE PREREQUISITES (Run these first!)
-----------------------------------------------------
* Update the system:
  sudo apt-get update

* Install Critical System Libraries:
  (Required for the HUD UI, Math, and I2C sensors)
  sudo apt-get install -y python3-tk python3-pil python3-pil.imagetk \
  libatlas-base-dev git gio-bin raspi-config python3-requests \
  python3-rpi.gpio python3-smbus2

* Force Install Python Packages:
  (Required for the Pi 5 / Bookworm OS environment)
  pip3 install Pillow RPi.bme280 --break-system-packages

2. CLONE REPOSITORY (No Password Required)
-----------------------------------------------------
* Use the HTTPS link to avoid username/password prompts.
  Make sure your repo is set to "Public" on GitHub.
  
  cd /home/pi
  git clone https://github.com/bsbachert/Sumner_Guard.git allsky_guard

3. HARDWARE CONFIG (Pi 5 Pins)
-----------------------------------------------------
* Enable I2C: sudo raspi-config -> Interface -> I2C -> Yes
* Wiring Checklist: 
  - ANEMOMETER: Brown (Pin 7/GPIO 4) | Blue (Pin 9/GND)
  - RAIN SENSOR: Signal -> GPIO 18 (Pin 12)
  - I2C (BME/MLX): SDA (Pin 3) | SCL (Pin 5)



4. RUN AUTOMATED INSTALLER
-----------------------------------------------------
cd /home/pi/allsky_guard
chmod +x install.sh
./install.sh

5. FIRST BOOT & SYNC
-----------------------------------------------------
1. sudo reboot
2. Open HUD -> Click [MAINT / DOSSIER]
3. Enter Radar ID (e.g., KTBW) and ClearSky ID (e.g., TampFL)
4. Click [SAVE] then click [SYNC].

=====================================================
                 PROJECT OVERVIEW
=====================================================
Sumner Guard is a specialized Raspberry Pi 5 Head-Up 
Display (HUD) for astronomical observatory management.

CORE CAPABILITIES:
* TELEMETRY: Real-time monitoring of Sky Temp, Ambient 
  Temp, Humidity, Pressure, Wind Speed, and Rain detection.
* SAFETY: Automated fail-safes (via guard.py) that 
  monitor internet heartbeats and Seestar connectivity 
  to trigger emergency roof closure if needed.
* IMAGING: Live integration of AllSky camera feeds, 
  NWS Doppler Radar, and ClearDarkSky astronomical clocks.
* MAINTENANCE: A smart tracking system that logs 
  operational hours and triggers a "Cleaning Reminder" 
  every 1,000 hours to ensure optical clarity.
* CONTROL: Rapid-launch buttons for INDIGO Sky, 
  Imager, and Seestar mobile mirroring.

The system is designed to be the "Single Source of Truth" 
for your observatory, ensuring both hardware safety 
and environmental awareness at a glance.
=====================================================