import smbus2, bme280, time, os
import RPi.GPIO as GPIO

# --- CONFIG ---
BME_ADDR = 0x76  
MLX_ADDR = 0x5A
WIND_PIN = 4   # Brown wire per your saved info
PATH_SENSORS = "/home/pi/allsky_guard/sensors.txt"

# Initialize Bus and GPIO
bus = smbus2.SMBus(1)
GPIO.setmode(GPIO.BCM)
GPIO.setup(WIND_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Wind Speed Pulse Counter
wind_pulses = 0
def count_wind(channel):
    global wind_pulses
    wind_pulses += 1

GPIO.add_event_detect(WIND_PIN, GPIO.FALLING, callback=count_wind)

def get_mlx_sky_temp():
    try:
        # Read raw word from MLX RAM address 0x07 (Object Temp)
        # We use a try block because MLX can be "noisy" on the I2C bus
        raw_data = bus.read_word_data(MLX_ADDR, 0x07)
        celsius = (raw_data * 0.02) - 273.15
        return (celsius * 9/5) + 32
    except Exception:
        return None

def main():
    global wind_pulses
    print(f"Worker started. Monitoring 0x76 and 0x5A...")
    
    while True:
        # 1. BME280 Data
        try:
            params = bme280.load_calibration_params(bus, BME_ADDR)
            data = bme280.sample(bus, BME_ADDR, params)
            amb_f = (data.temperature * 9/5) + 32
            amb_str = f"{amb_f:.1f} F"
            hum_str = f"{data.humidity:.1f} %"
            pre_str = f"{data.pressure:.1f} hPa"
        except:
            amb_str, hum_str, pre_str = "--", "--", "--"

        # 2. MLX90614 Data
        sky_val = get_mlx_sky_temp()
        sky_str = f"{sky_val:.1f} F" if sky_val is not None else "--"

        # 3. Wind Speed (3 second sample)
        wind_pulses = 0
        time.sleep(3)
        # Formula: 1.492 mph per pulse-per-second
        speed = (wind_pulses / 3) * 1.492
        wind_str = f"{speed:.1f} MPH"

        # 4. Write to File
        try:
            with open(PATH_SENSORS, "w") as f:
                f.write(f"SKY TEMP: {sky_str}\n")
                f.write(f"AMB TEMP: {amb_str}\n")
                f.write(f"HUMIDITY: {hum_str}\n")
                f.write(f"PRESSURE: {pre_str}\n")
                f.write(f"WIND SPD: {wind_str}\n")
                f.write(f"PRECIP: DRY\n") # Placeholder
            
            print(f"Update: Sky {sky_str} | Amb {amb_str} | Wind {wind_str}")
        except Exception as e:
            print(f"File Write Error: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
