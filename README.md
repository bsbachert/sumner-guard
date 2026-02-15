===============================================================================
                    SUMNER GUARD: OBSERVATORY HUD SYSTEM 
                          OFFICIAL TECHNICAL MANUAL
===============================================================================

1. SYSTEM OVERVIEW
------------------
Sumner Guard is a specialized Raspberry Pi 5 based Head-Up Display (HUD) 
designed for astronomical observatory management. It provides real-time 
environmental monitoring, sky imaging, and telescope hardware control.

CORE FEATURES:
- Real-time Allsky camera feed integration.
- Dynamic NWS Weather Radar with dark-mode optimization.
- **DYNAMIC LOCATION CLOCK**: Automatically fetches the ClearDarkSky clock 
  and forecast chart based on your saved Zip Code.
- Sensor telemetry (Sky Temp, Ambient, Humidity, Wind, Rain, Pressure).
- One-touch telescope control (INDIGO Sky, Imager, Seestar Mirroring).
- Google Sheets integration for long-term wind data logging.
- 1,000-hour Maintenance/Cleaning reminder system.

2. HARDWARE WIRING SPECIFICATIONS (Raspberry Pi 5)
--------------------------------------------------

ANEMOMETER (Wind Speed):
- **Brown Wire (Signal)**: GPIO 4 (Physical Pin 7)
- **Blue Wire (Ground)**:  GND (Physical Pin 9)
* Note: Software enables internal pull-up; no external resistor required.

BME280 (Ambient Temp/Hum/Pres) & MLX90614 (Sky Temp):
- VCC: 3.3V (Physical Pin 1)
- GND: Ground (Physical Pin 6)
- SDA: GPIO 2 (Physical Pin 3)
- SCL: GPIO 3 (Physical Pin 5)

RAIN SENSOR:
- Signal: GPIO 17 (Physical Pin 11)
- GND:    Physical Pin 14

3. DYNAMIC LOCATION & SYNC
--------------------------
The HUD no longer relies on hardcoded image links for specific cities. 

TO SET YOUR LOCATION:
1. Open the **MAINT / DOSSIER** window on the HUD.
2. Enter your **ZIP CODE** in the provided field.
3. Click **SAVE**.
4. Click **FORCE SYNC**. 

The system will use your Zip Code to calculate coordinates and download the 
exact astronomical clock and forecast chart for your position.

4. MAINTENANCE & ALERTS
-----------------------
- **Cleaning Reminder**: A popup will trigger every 1,000 operational hours 
  to remind you to clean the dome and sensors.
- **Resetting**: After cleaning, use the **RESET** button in the Dossier 
  window to clear the timer back to zero.

5. TROUBLESHOOTING
------------------
- **Missing Clock**: Ensure the `geopy` library is installed (`pip3 install geopy`).
- **Radar Fail**: Verify your 4-letter Station ID in the Dossier (e.g., KGRR).
- **Sensors "--"**: Check I2C wiring or run `sudo i2cdetect -y 1`.
===============================================================================