import RPi.GPIO as GPIO
import time
import os

PIN = 4
CALIBRATION = 1.492  # 1 pulse/sec = 1.492 mph. Adjust if needed.
SENSOR_FILE = "/home/pi/allsky_guard/sensors.txt"

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

pulse_count = 0

def count_pulse(channel):
    global pulse_count
    pulse_count += 1

GPIO.add_event_detect(PIN, GPIO.FALLING, callback=count_pulse)

print("Wind Sensor Active... Press Ctrl+C to stop.")

try:
    while True:
        pulse_count = 0
        time.sleep(5)  # Sample wind over 5 seconds
        
        # Calculate MPH
        wind_speed = (pulse_count / 5) * CALIBRATION
        
        # Read existing sensor data to keep other values
        lines = []
        if os.path.exists(SENSOR_FILE):
            with open(SENSOR_FILE, "r") as f:
                lines = f.readlines()
        
        # Update or add the Wind Speed line
        updated = False
        with open(SENSOR_FILE, "w") as f:
            for line in lines:
                if "WIND SPD" in line.upper():
                    f.write(f"WIND SPD: {wind_speed:.1f} mph\n")
                    updated = True
                else:
                    f.write(line)
            if not updated:
                f.write(f"WIND SPD: {wind_speed:.1f} mph\n")
                
except KeyboardInterrupt:
    GPIO.cleanup()
