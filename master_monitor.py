import time, os, RPi.GPIO as GPIO, requests

DATA_DIR = "/home/pi/allsky_guard"
WIND_LIMIT = 15.0
RAIN_PIN = 22
PARK_PIN = 18
CLOSE_RELAY = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(CLOSE_RELAY, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup([RAIN_PIN, PARK_PIN], GPIO.IN, pull_up_down=GPIO.PUD_UP)

def emergency_shutdown():
    try: requests.get("http://192.168.1.50/api/park", timeout=2)
    except: pass
    for _ in range(45):
        if GPIO.input(PARK_PIN) == GPIO.LOW:
            GPIO.output(CLOSE_RELAY, GPIO.LOW)
            time.sleep(1.5)
            GPIO.output(CLOSE_RELAY, GPIO.HIGH)
            break
        time.sleep(1)

def run_monitor():
    while True:
        if GPIO.input(RAIN_PIN) == GPIO.LOW:
            emergency_shutdown()
        time.sleep(5)

if __name__ == "__main__":
    run_monitor()
