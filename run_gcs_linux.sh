#!/bin/bash
# ==============================================================================
# TEAM EDITH - AIR MOUSE GCS (LINUX LAUNCHER)
# PS2: Autonomous GPS-Denied Indoor Search, Mapping & Survivor Localization
# ==============================================================================

echo "========================================================"
echo "  TEAM EDITH - AIR MOUSE GROUND CONTROL STATION (GCS)"
echo "  Target Platform: Linux (Ubuntu 22.04 / 24.04 LTS)"
echo "========================================================"

# Check if Python 3 and Tkinter are installed
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 not found. Installing..."
    sudo apt update && sudo apt install -y python3 python3-tk python3-pip
fi

# Run the Ground Control Station
echo "[*] Launching AirMouse GCS..."
python3 airmouse_gcs.py
