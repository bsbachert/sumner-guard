import smbus2, bme280, time, os, subprocess, threading

# --- CONFIG ---
BME_ADDR = 0x76  
MLX_ADDR = 0x5A
WIND_PIN = 5   
RAIN_PIN = 18  
ROOF_PIN = 17  
PATH_SENSORS = "/home/pi/allsky_guard/sensors.txt"
PATH_HOURS = "/home/pi/allsky_guard/hours.txt"

# --- GLOBAL PULSE COUNTER ---
wind_pulse_count = 0
last_pulse_time = 0

def wind_event_listener():
    global wind_pulse_count, last_pulse_time
    # Use pinctrl poll indefinitely and read its output live
    cmd = ["pinctrl", "poll", str(WIND_PIN)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    
    for line in proc.stdout:
        if "lo" in line:
            now = time.time()
            if (now - last_pulse_time) > 0.02: 
                wind_pulse_count += 1
                last_pulse_time = now

def init_hardware():
    try:
        # Give hardware time to settle on boot
        time.sleep(2) 
        subprocess.run(["pinctrl", "set", str(WIND_PIN), "ip", "pu"], check=True)
        subprocess.run(["pinctrl", "set", str(RAIN_PIN), "ip", "pu"], check=True)
        subprocess.run(["pinctrl", "set", str(ROOF_PIN), "op", "dl"], check=True)
        
        t = threading.Thread(target=wind_event_listener, daemon=True)
        t.start()
        
        return smbus2.SMBus(1)
    except:
        return None

def main():
    global wind_pulse_count
    bus = init_hardware()
    last_check = time.time()
    
    while True:
        # Keep the 5-second sample for wind accuracy
        time.sleep(5)
        
        pulses = wind_pulse_count
        wind_pulse_count = 0  
        
        # 1. Wind & Rain (GPIO)
        try:
            rain_raw = subprocess.check_output(["pinctrl", "get", str(RAIN_PIN)], text=True)
            is_wet = "lo" in rain_raw.lower()
        except: is_wet = False

        speed = (pulses / 5) * 2.25
        if speed > 100.0: speed = 0.0 
        
        # 2. Ambient Data (BME280) - Independent Try
        amb_str, hum_str, pre_str = "--", "--", "--"
        amb_val, hum_val = None, None
        if bus:
            try:
                params = bme280.load_calibration_params(bus, BME_ADDR)
                data = bme280.sample(bus, BME_ADDR, params)
                amb_val = (data.temperature * 9/5) + 32
                hum_val = data.humidity
                amb_str = f"{amb_val:.1f} F"
                hum_str = f"{hum_val:.1f} %"
                pre_str = f"{data.pressure:.1f} hPa"
            except Exception: pass

        # 3. Sky Temp (MLX90614) - Independent Try
        sky_str = "ORD-SUN"
        if bus:
            try:
                raw_sky = bus.read_word_data(MLX_ADDR, 0x07)
                sky_f = ((raw_sky * 0.02) - 273.15) * 9/5 + 32
                sky_str = f"{sky_f:.1f} F"
            except Exception: pass

        # 4. Roof Control Logic
        if is_wet or speed > 20.0:
            subprocess.run(["pinctrl", "set", str(ROOF_PIN), "dh"])
            status = "CLOSED/LOCKED"
        else:
            subprocess.run(["pinctrl", "set", str(ROOF_PIN), "dl"])
            status = "OPEN/SAFE"

        # 5. Hours Tracking
        now = time.time()
        elapsed = (now - last_check) / 3600.0
        last_check = now
        total = 0.0
        try:
            if os.path.exists(PATH_HOURS):
                with open(PATH_HOURS, "r") as hf: total = float(hf.read().strip())
            with open(PATH_HOURS, "w") as hf: hf.write(f"{total + elapsed:.4f}")
        except: pass

        # 6. Write to HUD (matching the format hud.py expects)
        try:
            with open(PATH_SENSORS, "w") as f:
                f.write(f"ROOF: {status}\n")
                f.write(f"SKY TEMP: {sky_str}\n")
                f.write(f"AMB TEMP: {amb_str}\n")
                f.write(f"HUMIDITY: {hum_str}\n")
                f.write(f"PRESSURE: {pre_str}\n")
                f.write(f"WIND SPD: {speed:.1f} MPH\n")
                f.write(f"PRECIP: {'WET' if is_wet else 'DRY'}\n")
                f.write(f"TOTAL RUN: {total:.1f} HRS\n")
        except: pass

if __name__ == "__main__":
    main()
