import smbus2, bme280, time, os, subprocess, threading, math, serial

# --- CONFIG ---
BME_ADDR = 0x76  
# MLX_ADDR = 0x5A  # Replaced by Arduino Serial logic
WIND_PIN = 4   
RAIN_PIN = 18  
ROOF_PIN = 17  
DEW_HEATER_PIN = 12  # PWM Signal to MOSFET [cite: 2026-02-03]
USB_PORT = "/dev/ttyUSB0" # Arduino Source
PATH_SENSORS = "/home/pi/allsky_guard/sensors.txt"
PATH_HOURS = "/home/pi/allsky_guard/hours.txt"

# --- GLOBAL PULSE COUNTER ---
wind_pulse_count = 0
last_pulse_time = 0
latest_sky_temp = "WAIT..." # Global to store Arduino data

def connect_serial():
    """Establishes connection to the Arduino"""
    try:
        # Standard baud for your Arduino sky temp setup
        s = serial.Serial(USB_PORT, 9600, timeout=1)
        time.sleep(2) # Wait for Arduino reset
        return s
    except:
        return None

def wind_event_listener():
    global wind_pulse_count, last_pulse_time
    # Anemometer: brown and blue wires to GPIO 4 and Ground [cite: 2026-02-03]
    cmd = ["pinctrl", "poll", str(WIND_PIN)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, bufsize=1)
    for line in iter(proc.stdout.readline, ''):
        if "lo" in line:
            now = time.time()
            if (now - last_pulse_time) > 0.01: 
                wind_pulse_count += 1
                last_pulse_time = now

def init_hardware():
    try:
        time.sleep(2) 
        
        # Explicitly set GPIO 12 as Output and Drive Low initially
        subprocess.run(["sudo", "pinctrl", "set", str(DEW_HEATER_PIN), "op", "dl"], check=True)
        
        # Initialize existing pins
        subprocess.run(["sudo", "pinctrl", "set", str(WIND_PIN), "ip", "pu"], check=True)
        subprocess.run(["sudo", "pinctrl", "set", str(RAIN_PIN), "ip", "pu"], check=True)
        subprocess.run(["sudo", "pinctrl", "set", str(ROOF_PIN), "op", "dl"], check=True)
        
        t = threading.Thread(target=wind_event_listener, daemon=True)
        t.start()
        return smbus2.SMBus(1)
    except Exception as e:
        print(f"Hardware Init Failed: {e}")
        return None

def set_heater_state(is_on):
    state = "dh" if is_on else "dl"
    try:
        subprocess.run(["sudo", "pinctrl", "set", str(DEW_HEATER_PIN), "op", state], check=True)
    except:
        pass

def main():
    global wind_pulse_count, latest_sky_temp
    bus = init_hardware()
    ser = connect_serial()
    last_check = time.time()
    
    while True:
        # --- 1. READ ARDUINO (Sky Temp) ---
        if ser:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    # Expecting Arduino to send "SKY TEMP: XX.X F"
                    if "SKY TEMP" in line.upper():
                        latest_sky_temp = line.split(":")[-1].strip()
            except:
                ser.close()
                ser = connect_serial()
        else:
            ser = connect_serial()
            latest_sky_temp = "OFFLINE"

        time.sleep(5)
        pulses = wind_pulse_count
        wind_pulse_count = 0  
        
        try:
            rain_raw = subprocess.check_output(["pinctrl", "get", str(RAIN_PIN)], text=True)
            is_wet = "lo" in rain_raw.lower()
        except: is_wet = False

        speed = (pulses / 5) * 2.25
        if speed > 100.0: speed = 0.0 
        
        amb_f, hum_val, pre_str = None, None, "--"
        if bus:
            try:
                params = bme280.load_calibration_params(bus, BME_ADDR)
                data = bme280.sample(bus, BME_ADDR, params)
                amb_f = (data.temperature * 9/5) + 32
                hum_val = data.humidity
                pre_str = f"{data.pressure:.1f} hPa"
            except: pass

        # --- 2. DEW HEATER LOGIC ---
        heater_status = "OFF"
        if amb_f is not None and hum_val is not None:
            T = (amb_f - 32) * 5/9
            gamma = (math.log(hum_val/100) + ((17.27 * T) / (237.3 + T)))
            dew_f = ((237.3 * gamma) / (17.27 - gamma) * 9/5) + 32
            
            # Trigger if Ambient Temp is within 5 degrees of Dew Point
            if (amb_f - dew_f) <= 5.0:
                set_heater_state(True)
                heater_status = "ON (DEW RISK)"
            else:
                set_heater_state(False)
        
        if is_wet or speed > 20.0:
            subprocess.run(["pinctrl", "set", str(ROOF_PIN), "dh"])
            status = "CLOSED/LOCKED"
        else:
            subprocess.run(["pinctrl", "set", str(ROOF_PIN), "dl"])
            status = "OPEN/SAFE"

        now = time.time()
        elapsed = (now - last_check) / 3600.0
        last_check = now
        total = 0.0
        try:
            if os.path.exists(PATH_HOURS):
                with open(PATH_HOURS, "r") as hf: total = float(hf.read().strip())
            with open(PATH_HOURS, "w") as hf: hf.write(f"{total + elapsed:.4f}")
        except: pass

        # --- 3. WRITE TO FILE ---
        try:
            with open(PATH_SENSORS, "w") as f:
                f.write(f"ROOF: {status}\n")
                f.write(f"HEATER: {heater_status}\n")
                f.write(f"SKY TEMP: {latest_sky_temp}\n") 
                f.write(f"AMB TEMP: {f'{amb_f:.1f} F' if amb_f else '--'}\n")
                f.write(f"HUMIDITY: {f'{hum_val:.1f} %' if hum_val else '--'}\n")
                f.write(f"PRESSURE: {pre_str}\n")
                f.write(f"WIND SPD: {speed:.1f} MPH\n")
                f.write(f"PRECIP: {'WET' if is_wet else 'DRY'}\n")
                f.write(f"TOTAL RUN: {total:.1f} HRS\n")
        except: pass

if __name__ == "__main__":
    main()
