import RPi.GPIO as GPIO
import time
import os

# --- CONFIGURATION ---
RAIN_PIN = 18          # RG-11 (Input)
MOSFET_PIN = 17        # Noyito Module (Output)
SENSOR_FILE = "/home/pi/allsky_guard/sensors.txt"
HOLD_TIME = 5          # Minimum seconds to keep MOSFET ON after rain is detected

# --- GPIO SETUP ---
GPIO.setmode(GPIO.BCM)
# High (3.3V) = Dry, Low (0V) = Wet (via RG-11 Relay to Ground)
GPIO.setup(RAIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Output for the MOSFET module
GPIO.setup(MOSFET_PIN, GPIO.OUT, initial=GPIO.LOW)

def update_hud_file(status):
    """Updates only the RAIN DET line in sensors.txt to prevent double lines."""
    lines = []
    if os.path.exists(SENSOR_FILE):
        try:
            with open(SENSOR_FILE, 'r') as f:
                lines = f.readlines()
        except:
            pass

    new_lines = []
    found = False
    
    # Process existing lines to find and update the Rain entry
    for line in lines:
        if "RAIN DET" in line.upper():
            new_lines.append(f"RAIN DET: {status}\n")
            found = True
        elif line.strip():  # Keep all other sensor data (Temp, Hum, etc.)
            new_lines.append(line)
    
    # If RAIN DET wasn't in the file yet, add it to the end
    if not found:
        new_lines.append(f"RAIN DET: {status}\n")

    try:
        with open(SENSOR_FILE, 'w') as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"File Error: {e}")

print("--- Sumner Observatory Rain Guard Active ---")
print(f"Monitoring RG-11 on GPIO {RAIN_PIN}")
print(f"Controlling MOSFET on GPIO {MOSFET_PIN}")

try:
    last_status = None
    
    while True:
        # Read sensor (GPIO.LOW means the relay closed due to rain)
        is_raining = GPIO.input(RAIN_PIN) == GPIO.LOW
        
        if is_raining:
            # Action: Only update and log if status changed
            if last_status != "WET":
                print("⚠️  RAIN DETECTED! Activating MOSFET.")
                update_hud_file("WET")
                last_status = "WET"
            
            # Fire the MOSFET
            GPIO.output(MOSFET_PIN, GPIO.HIGH)
            
            # Hold the state for a few seconds to prevent rapid flickering
            time.sleep(HOLD_TIME)
        else:
            # Action: Only update and log if status changed
            if last_status != "DRY":
                print("☀️  System Dry. Deactivating MOSFET.")
                update_hud_file("DRY")
                last_status = "DRY"
            
            # Turn off MOSFET
            GPIO.output(MOSFET_PIN, GPIO.LOW)
            
            # Small sleep to keep CPU usage low
            time.sleep(1)

except KeyboardInterrupt:
    print("\nShutting down Rain Guard...")
    GPIO.cleanup()
