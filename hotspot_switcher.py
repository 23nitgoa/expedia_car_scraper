from datetime import datetime
import subprocess
import time
import os
import socket

STATE_FILE = "hotspot_state.txt"

def get_next_hotspot():
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            f.write("Redmi Note 10 Pro")
        return "Redmi Note 10 Pro"

    with open(STATE_FILE, "r") as f:
        last = f.read().strip()

    next_hotspot = "Motorola RG" if last == "Redmi Note 10 Pro" else "Redmi Note 10 Pro"

    with open(STATE_FILE, "w") as f:
        f.write(next_hotspot)

    return next_hotspot

def wait_for_internet(timeout=60):
    print("[INFO] Waiting for internet connectivity...")
    start = datetime.now()
    while (datetime.now() - start).seconds < timeout:
        try:
            socket.gethostbyname('www.google.com')
            print("[INFO] Internet is available.")
            return True
        except socket.gaierror:
            time.sleep(1)
    raise Exception("[ERROR] Internet not available after switching hotspot.")

def switch_to_hotspot(profile):
    print(f"[INFO] Attempting to switch to hotspot: {profile}")
    
    for p in ["Redmi Note 10 Pro", "Motorola RG"]:
        subprocess.run(["netsh", "wlan", "set", "profileparameter", f"name={p}", "connectionmode=manual"], capture_output=True)

    subprocess.run(["netsh", "wlan", "disconnect"], capture_output=True)
    time.sleep(5)

    result = subprocess.run(["netsh", "wlan", "connect", f"name={profile}"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[SUCCESS] Connected to {profile}")
        time.sleep(5)
        return True
    else:
        print(f"[ERROR] Failed to connect to {profile}: {result.stderr.strip()}")
        return False

def rotate_hotspot():
    hotspot = get_next_hotspot()
    if switch_to_hotspot(hotspot):
        wait_for_internet()
