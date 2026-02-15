=====================================================
    SUMNER GUARD: OBSERVATORY HUD SYSTEM
          OFFICIAL SETUP & INSTALLATION
=====================================================

1. PREREQUISITES (Do these first!)
-----------------------------------------------------
* Hardware Wiring (Pi 5):
  - ANEMOMETER: Brown (Signal) -> GPIO 4 | Blue (GND) -> Pin 9
  - RAIN SENSOR: Signal -> GPIO 18
  - I2C SENSORS: SDA -> GPIO 2 | SCL -> GPIO 3

* Enable I2C:
  - Run: sudo raspi-config
  - Navigate to: Interface Options -> I2C -> Yes
  - Finish and Exit.

2. ESSENTIAL FILE LIST (Clean up your folder!)
-----------------------------------------------------
Keep ONLY these files in /home/pi/allsky_guard to avoid conflicts:

- hud.py              (Main Dashboard)
- install.sh          (Setup Script)
- get_radar.py        (Sync Engine)
- sensor_worker.py    (Primary Data Collector)
- guard.py            (Connection Monitor)
- master_monitor.py   (Safety Engine)
- close_dome.sh       (Hardware Relay Trigger)
- sumner_sync.service (Systemd automation)
- sumner_sync.timer   (Hourly schedule)

*NOTE: You can delete update_sensors.py, wind_sensor.py, and 
rain_watcher.py as they are now merged into sensor_worker.py.

3. GITHUB INSTALLATION COMMANDS
-----------------------------------------------------
Open your terminal and run these in order:

cd /home/pi
git clone https://github.com/bsbachert/Sumner_Guard.git allsky_guard
cd allsky_guard
chmod +x install.sh
./install.sh

4. POST-INSTALLATION
-----------------------------------------------------
1. REBOOT the Pi: sudo reboot
2. Launch HUD (if it doesn't auto-boot).
3. Open MAINT / DOSSIER.
4. Enter Radar ID (e.g., KTBW) and ClearSky ID (e.g., TampFL).
5. Click SAVE then click SYNC.

5. MAINTENANCE LOGIC
-----------------------------------------------------
- Cleaning Alert: Triggers automatically at 1,000 hours.
- Resetting: Use the RESET button in the Dossier after cleaning.
=====================================================