import smbus2, bme280, time, os, subprocess, threading, math, serial
import RPi.GPIO as GPIO

# --- CONFIG ---
ROOF_PIN = 17  
DEW_HEATER_PIN = 12  
USB_PORT = "/dev/ttyUSB0" 
PATH_SENSORS = "/home/pi/allsky_guard/sensors.txt"
PATH_HOURS = "/home/pi/allsky_guard/hours.txt"

# --- GLOBAL DATA HOLDERS ---
latest_sky_temp = "WAIT..."
latest_amb_temp = None
latest_humidity = None
latest_pressure = "--"
latest_wind_speed = 0.0
latest_rain_state = "DRY"

GPIO.setmode(GPIO.BCM)

def connect_serial():
    try:
        if not os.path.exists(USB_PORT): return None
        s = serial.Serial(USB_PORT, 9600, timeout=2)
        time.sleep(2)
        s.reset_input_buffer()
        return s
    except: return None

def arduino_reader():
    global latest_sky_temp, latest_wind_speed, latest_amb_temp, latest_humidity, latest_pressure, latest_rain_state
    ser = connect_serial()
    while True:
        if ser and ser.is_open:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if "SKY:" in line:
                        data = dict(item.split(":") for item in line.split(","))
                        latest_sky_temp = f"{data.get('SKY', 'WAIT...')} F"
                        latest_pressure = f"{data.get('PRES', '--')} hPa"
                        latest_rain_state = "WET" if data.get('RAIN') == "1" else "DRY"
                        try:
                            latest_amb_temp = float(data.get('AMB', 0.0))
                            latest_humidity = float(data.get('HUM', 0.0))
                            latest_wind_speed = float(data.get('WIND', 0.0))
                        except: pass
            except:
                ser = None
        else:
            time.sleep(5)
            ser = connect_serial()
        time.sleep(0.1)

threading.Thread(target=arduino_reader, daemon=True).start()
last_check = time.time()

while True:
    time.sleep(5)
    
    # Values now come entirely from the Arduino thread
    amb_f = latest_amb_temp
    hum_val = latest_humidity
    speed = latest_wind_speed
    is_wet = (latest_rain_state == "WET")
    
    heater_status = "OFF"
    if amb_f and hum_val:
        T = (amb_f - 32) * 5/9
        gamma = (math.log(hum_val/100) + ((17.27 * T) / (237.3 + T)))
        dew_f = ((237.3 * gamma) / (17.27 - gamma) * 9/5) + 32
        if (amb_f - dew_f) <= 5.0:
            subprocess.run(["sudo", "pinctrl", "set", str(DEW_HEATER_PIN), "op", "dh"])
            heater_status = "ON (DEW RISK)"
        else:
            subprocess.run(["sudo", "pinctrl", "set", str(DEW_HEATER_PIN), "op", "dl"])

    # Safety: Close roof if wet or windy
    status = "CLOSED/LOCKED" if (is_wet or speed > 20.0) else "OPEN/SAFE"
    subprocess.run(["pinctrl", "set", str(ROOF_PIN), "dh" if status == "CLOSED/LOCKED" else "dl"])

    # Maintenance Timer [cite: 2026-01-17]
    now = time.time()
    elapsed = (now - last_check) / 3600.0
    last_check = now
    total = 0.0
    try:
        if os.path.exists(PATH_HOURS):
            with open(PATH_HOURS, "r") as hf: total = float(hf.read().strip())
        new_total = total + elapsed
        with open(PATH_HOURS, "w") as hf: hf.write(f"{new_total:.4f}")
    except: new_total = 0.0

    # Write final sensors.txt
    try:
        with open(PATH_SENSORS, "w") as f:
            f.write(f"ROOF: {status}\nHEATER: {heater_status}\nSKY TEMP: {latest_sky_temp}\n") 
            f.write(f"AMB TEMP: {f'{amb_f:.1f} F' if amb_f else '--'}\n")
            f.write(f"HUMIDITY: {f'{hum_val:.1f} %' if hum_val else '--'}\n")
            f.write(f"PRESSURE: {latest_pressure}\n")
            f.write(f"WIND SPD: {speed:.1f} MPH\n")
            f.write(f"PRECIP: {latest_rain_state}\n")
            f.write(f"TOTAL RUN: {new_total:.1f} HRS\n")
            if new_total >= 1000.0: f.write("MAINT: CLEANING REQUIRED\n")
    except Exception as e: print(f"Write Error: {e}")