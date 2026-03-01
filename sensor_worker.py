import smbus2, bme280, time, os, subprocess, threading, math

# --- CONFIG ---
BME_ADDR = 0x76  
MLX_ADDR = 0x5A
WIND_PIN = 4   
RAIN_PIN = 18  
ROOF_PIN = 17  
DEW_HEATER_PIN = 12  # PWM Signal to MOSFET [cite: 2026-02-03]
PATH_SENSORS = "/home/pi/allsky_guard/sensors.txt"
PATH_HOURS = "/home/pi/allsky_guard/hours.txt"

# --- GLOBAL PULSE COUNTER ---
wind_pulse_count = 0
last_pulse_time = 0

def wind_event_listener():
    global wind_pulse_count, last_pulse_time
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
        # Give the system a moment to initialize the RP1 chip on Pi 5
        time.sleep(2) 
        
        # Explicitly set GPIO 12 as Output and Drive Low (OFF) initially
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
    """Sets MOSFET state. 'dh' (Drive High) is 100% power, 'dl' (Drive Low) is OFF."""
    state = "dh" if is_on else "dl"
    try:
        # On Pi 5, we include 'op' to ensure the pin remains in Output mode
        subprocess.run(["sudo", "pinctrl", "set", str(DEW_HEATER_PIN), "op", state], check=True)
    except:
        pass

def main():
    global wind_pulse_count
    bus = init_hardware()
    last_check = time.time()
    
    while True:
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

        sky_str = "--"
        if bus:
            try:
                raw_sky = bus.read_word_data(MLX_ADDR, 0x07)
                sky_f = ((raw_sky * 0.02) - 273.15) * 9/5 + 32
                sky_str = f"{sky_f:.1f} F"
            except: pass

        # --- DEW HEATER LOGIC ---
        heater_status = "OFF"
        if amb_f is not None and hum_val is not None:
            # Calculate Dew Point
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

        try:
            with open(PATH_SENSORS, "w") as f:
                f.write(f"ROOF: {status}\n")
                f.write(f"HEATER: {heater_status}\n")
                f.write(f"SKY TEMP: {sky_str}\n")
                f.write(f"AMB TEMP: {f'{amb_f:.1f} F' if amb_f else '--'}\n")
                f.write(f"HUMIDITY: {f'{hum_val:.1f} %' if hum_val else '--'}\n")
                f.write(f"PRESSURE: {pre_str}\n")
                f.write(f"WIND SPD: {speed:.1f} MPH\n")
                f.write(f"PRECIP: {'WET' if is_wet else 'DRY'}\n")
                f.write(f"TOTAL RUN: {total:.1f} HRS\n")
        except: pass

if __name__ == "__main__":
    main()
