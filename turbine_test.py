import RPi.GPIO as GPIO
import time

TURBINE_PIN = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(TURBINE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# 'bouncetime' in milliseconds (20ms ignores 'ghost' signals)
GPIO.add_event_detect(TURBINE_PIN, GPIO.FALLING, bouncetime=20)

print("🌬️ Turbine Filter Active. Spin it now...")

count = 0
try:
    while True:
        if GPIO.event_detected(TURBINE_PIN):
            count += 1
            print(f"✅ Real Pulse: {count}")
        time.sleep(0.01)
except KeyboardInterrupt:
    GPIO.cleanup()
