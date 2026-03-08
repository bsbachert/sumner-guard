#!/usr/bin/env python3
import time
import os
import PyIndi
import subprocess
from datetime import datetime

# --- CONFIG ---
DATA_DIR = "/home/pi/allsky_guard"
HOURS_FILE = f"{DATA_DIR}/hours.txt"
SENSOR_FILE = f"{DATA_DIR}/sensors.txt"
INDI_HOST = "127.0.0.1"
INDI_PORT = 7624
UPDATE_INTERVAL = 60 # Check status every 60 seconds
FAILSAFE_LIMIT = 5   # Minutes of internet loss before parking
PING_TARGET = "8.8.8.8"

# Ensure directory exists
os.makedirs(DATA_DIR, exist_ok=True)

class OperationGuard:
    def __init__(self):
        self.offline_count = 0
        try:
            self.indi = PyIndi.INDIClient()
        except AttributeError:
            self.indi = PyIndi.BaseClient()
        
        self.indi.setServer(INDI_HOST, INDI_PORT)
        self.indi.connectServer()

    def check_internet(self):
        """Pings Google DNS to verify internet connectivity"""
        try:
            subprocess.check_output(["ping", "-c", "1", "-W", "2", PING_TARGET])
            return True
        except subprocess.CalledProcessError:
            return False

    def get_park_status(self):
        """Returns True if telescope is PARKED"""
        try:
            device = self.indi.getDevice("ZWO Seestar")
            if not device: return True
            park_prop = device.getSwitch("TELESCOPE_PARK")
            # Index 1 is UNPARK. If it's ON, we are NOT parked.
            return not (park_prop[1].s == PyIndi.ISS_ON)
        except:
            return True 

    def park_and_close_sequence(self):
        """1-Minute Delayed Shutdown Sequence"""
        print("CRITICAL: Internet Lost. Parking Seestar first...")
        # Command Seestar to Park
        os.system(f"indi_setprop -p {INDI_PORT} 'ZWO Seestar.TELESCOPE_PARK.PARK=On'")
        
        # Wait 60 seconds for the arm to lay flat
        time.sleep(60)
        
        # Command Roof to Close (Update 'Roof.CONTACTOR' to match your driver)
        os.system(f"indi_setprop -p {INDI_PORT} 'Roof.CONTACTOR.RELAISE_CLOSE=On'")
        print("Safety sequence complete: Seestar Parked, Roof Closed.")

    def update_hud_bridge(self, internet_status):
        """Writes data to a file for the HUD to read"""
        try:
            with open(SENSOR_FILE, "w") as f:
                f.write(f"INTERNET: {internet_status}\n")
                f.write(f"ROOF: CHECKING...\n") # Future sensor input
                f.write(f"LAST SYNC: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"HUD Bridge Error: {e}")

    def increment_hours(self, seconds):
        """Tracks the 1,000 hour maintenance window"""
        try:
            if not os.path.exists(HOURS_FILE):
                with open(HOURS_FILE, "w") as f: f.write("0.0")
            
            with open(HOURS_FILE, "r") as f:
                content = f.read().strip()
                current_hrs = float(content) if content else 0.0
            
            with open(HOURS_FILE, "w") as f:
                f.write(f"{current_hrs + (seconds / 3600.0):.4f}")
        except:
            pass

    def run(self):
        print("Guard active: Monitoring Seestar, Internet, and Maintenance...")
        while True:
            # 1. Update maintenance hours if unparked
            is_parked = self.get_park_status()
            if not is_parked:
                self.increment_hours(UPDATE_INTERVAL)

            # 2. Check Internet Heartbeat
            online = self.check_internet()
            status_text = "ONLINE" if online else f"OFFLINE ({self.offline_count}m)"
            self.update_hud_bridge(status_text)

            if online:
                self.offline_count = 0
            else:
                self.offline_count += 1
                print(f"Internet connectivity lost: {self.offline_count} min(s)")

            # 3. Trigger Fail-safe
            if self.offline_count >= FAILSAFE_LIMIT:
                if not is_parked:
                    self.park_and_close_sequence()
                else:
                    # Even if parked, ensure roof is closed if internet stays down
                    os.system(f"indi_setprop -p {INDI_PORT} 'Roof.CONTACTOR.RELAISE_CLOSE=On'")

            time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    guard = OperationGuard()
    guard.run()
