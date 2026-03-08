#!/bin/bash

# --- CONFIG ---
LOGFILE="/home/pi/allsky_guard/dome_log.txt"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# --- LOGGING ---
echo "[$TIMESTAMP] RAIN DETECTED - INITIATING EMERGENCY CLOSE" >> $LOGFILE

# --- HARDWARE TRIGGER ---
# We will use GPIO 18 (Pin 12) to trigger your dome motor relay.
# Adjust the pin number if your motor is on a different pin.

# Initialize Pin 18 as output
raspi-gpio set 18 op

# Set Pin 18 HIGH to trigger the relay/motor
raspi-gpio set 18 dh

# Hold the trigger for 1 second (simulating a button press)
sleep 1

# Set Pin 18 LOW again
raspi-gpio set 18 dl

echo "[$TIMESTAMP] CLOSE COMMAND SENT SUCCESSFULLY" >> $LOGFILE
