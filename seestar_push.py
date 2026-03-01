import subprocess
import time

def trigger_bot():
    mac = "E1:6A:83:06:38:48"
    char_path = "/org/bluez/hci0/dev_E1_6A_83_06_38_48/service000e/char0012"
    
    # 57 01 = The basic Press command. 
    # The bot will now use your 6s app setting automatically.
    press_hex = "0x57 0x01"

    print(f"Gemini: Triggering 6-second Seestar power-up...")
    
    proc = subprocess.Popen(
        ['bluetoothctl'], 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        text=True
    )

    def send(cmd, delay=1.0):
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()
        time.sleep(delay)

    try:
        # 1. Connect
        send(f"connect {mac}", delay=4) 
        
        # 2. Navigate to the write handle
        send("menu gatt")
        send(f"select-attribute {char_path}")
        
        # 3. Trigger the action
        print("Command sent! Waiting for 6-second hold to finish...")
        send(f"write \"{press_hex}\"")
        
        # We wait 8 seconds total to allow the mechanical move to finish 
        # before we disconnect the Bluetooth link.
        time.sleep(8)
        
        send("quit")
        print("Sequence complete. Clear skies, Brian!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        proc.terminate()

if __name__ == "__main__":
    trigger_bot()
