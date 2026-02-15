=====================================================
    SUMNER GUARD: OBSERVATORY HUD SYSTEM
          OFFICIAL SETUP & INSTALLATION
=====================================================

1. HARDWARE PREREQUISITES (Pi 5 Wiring)
-----------------------------------------------------
* ANEMOMETER: Brown (Signal) -> GPIO 4 | Blue (GND) -> Pin 9
* RAIN SENSOR: Signal -> GPIO 18
* I2C SENSORS: SDA -> GPIO 2 | SCL -> GPIO 3



2. SOFTWARE PREREQUISITES (System Configuration)
-----------------------------------------------------
Before running the installer, run these commands manually:

* Enable I2C Interface:
  - Run: sudo raspi-config
  - Navigate to: Interface Options -> I2C -> Yes
  - Finish and Reboot.

* Update Package List:
  - Run: sudo apt-get update

* Install System Libraries (Required for UI and Math):
  - Run: sudo apt-get install -y python3-tk python3-pil python3-pil.imagetk \
         libatlas-base-dev gio-bin git

3. THE ESSENTIAL FILE LIST
-----------------------------------------------------
Keep ONLY these files in /home/pi/allsky_guard:

- hud.py              (Main Dashboard UI)
- install.sh          (Automated Installer)
- get_radar.py        (Image Sync Engine)
- sensor_worker.py    (Primary Data Collector)
- guard.py            (Connection Monitor)
- master_monitor.py   (Safety Engine)
- close_dome.sh       (Hardware Relay Trigger)
- sumner_sync.service (Systemd automation)
- sumner_sync.timer   (Hourly schedule)

4. GITHUB INSTALLATION COMMANDS
-----------------------------------------------------
cd /home/pi
git clone https://github.com/bsbachert/Sumner_Guard.git allsky_guard
cd allsky_guard
chmod +x install.sh
./install.sh

5. FINAL HUD CONFIGURATION
-----------------------------------------------------
1. Reboot: sudo reboot
2. Open HUD -> Click [MAINT / DOSSIER]
3. Enter Radar ID (Examples are (KGRR) and ClearSky ID (HwkHlObMI)
4. Click [SAVE] then [SYNC].
=====================================================