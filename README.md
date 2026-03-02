
<img width="1918" height="926" alt="Screenshot 2026-03-01 194741" src="https://github.com/user-attachments/assets/e9ecd347-c0c8-4405-b138-a200be36ab67" />


An integrated automation and monitoring suite for a remote Seestar S50 observatory, powered by a Raspberry Pi 5 (4GB). This system manages everything from proactive dew prevention to structural roof automation, ensuring the telescope is protected and accessible from anywhere in the world.

🔭 Project Overview
This software provides a centralized "Heads Up Display" (HUD) and a background worker system. The Pi 5 is mounted directly inside the AllSky camera housing, which is secured to the observatory structure. The system is designed for high-availability, capable of running on Solar or Grid power, requiring only a WiFi internet connection for global remote access.

🚀 Key Features
Dual-MOSFET Control:
Heater: PWM-driven proactive dew prevention using a 5°F safety buffer.
Roof: Logic-level control for a 20" Linear Actuator to open/close the observatory roof via the HUD.
Remote Power Management: Integration with a SwitchBot to remotely trigger the Seestar S50's physical power button.
Telescope Control: Full integration with Seestar_Alp for remote telescope operations.
Global Access: Fully compatible with Raspberry Pi Connect and VNC for real-time control from anywhere.
Environmental Safety: * Wind Guard: Automatic roof closure if wind speeds exceed 20 MPH.
Rain Guard: Instant lockdown upon precipitation detection.

🛠 Hardware Configuration
Component
Connection / Pin
Purpose
Anemometer
GPIO 4
Wind Speed Monitoring
Dew Heater
GPIO 12 (MOSFET 1)
Proactive Condensation Prevention
Roof Actuator
GPIO 17 (MOSFET 2)
20" Actuator Drive (Open/Close)
Rain Sensor
GPIO 18
Precipitation Detection
SwitchBot
Bluetooth (BLE)
Seestar Power On/Off
BME280 / MLX90614
I2C Bus
Ambient & Sky Temperature

🌡 Dew Prevention Logic
The system proactively calculates the dew point. If the ambient temperature falls within 5°F of the dew point, the Pi 5 engages the MOSFET on GPIO 12:

This ensures the optics remain clear before moisture can settle.

📦 Software Structure
hud.py: The primary GUI providing the visual dashboard and manual roof/power controls.

sensor_worker.py: The background engine handling sensor data, wind pulse counting, and automated safety logic.

seestar_push.py: The Bluetooth script for SwitchBot/Fingerbot interaction.

🔧 Installation & Remote Access
Clone & Setup:
Bash
git clone https://github.com/bsbachert/Seestar-Remote-Observatory-Control.git

cd sumner_guard
./install.sh

Connectivity: Ensure Raspberry Pi Connect or VNC Server is enabled via raspi-config.

Power: Designed for 12V DC input 5A, compatible with solar charge controllers or standard grid-tie adapters.

This is a work in Progress. Adding more as I build the Observatory.
