# 🛸 TEAM EDITH | AirMouse Ground Control Station (GCS)
**Autonomous GPS-Denied Indoor Search, Mapping & Survivor Localization Challenge**  
*NIDAR AirMouse Challenge — Track 1 (PS2)*

---

## 📌 Overview
The **TEAM EDITH AirMouse Ground Control Station (GCS)** is an ultra-lightweight, high-performance tactical monitoring station designed for autonomous drones operating in GPS-denied indoor disaster corridors.

### 🌟 Key Features
- **2D Robotic SLAM Canvas:** High-contrast pitch-black point-cloud visualization, rotating LiDAR cone, 1m metric grid (A–O & 1–15), and dynamic flight trajectory ribbon.
- **Survivor Localization System:** Real-time 6-survivor tracker (T1–T6) with discrete arena coordinate mapping (e.g. `Grid [C-4]`) and confidence ratings.
- **Camera HUD & Computer Vision:** 30 FPS video feed with OSD timestamp, rec indicator, and YOLOv8 survivor detection bounding box.
- **Attitude & Heading System:** Precision 360° heading compass with pitch/roll indicators and numeric degree readout.
- **4-System Hardware Health Matrix:** Live monitoring of IMU, LiDAR (RPLiDAR A2), Camera, and Telemetry links.
- **Audio Alert System:** Tactical sonar pulse sound on survivor detection and 3-tone victory chime upon completing mission objectives.
- **Safety & Mission Controls:** Single-click Autonomous Takeoff and Emergency Abort (RTL) to Entry/Exit LZ.

---

## 🚀 Quick Start

### 🐧 Running on Linux (Ubuntu 22.04 / 24.04 LTS)
Ensure Python 3 and Tkinter are available:
```bash
sudo apt update
sudo apt install -y python3 python3-tk
```
Run the application:
```bash
python3 airmouse_gcs.py
```
*Or use the launcher script:*
```bash
chmod +x run_gcs_linux.sh
./run_gcs_linux.sh
```

### 🪟 Running on Windows
Simply run:
```cmd
python airmouse_gcs.py
```
*Or double-click:* `run_gcs_windows.bat`

---

## 📁 Repository Structure
```
├── airmouse_gcs.py         # Main GCS application engine
├── run_gcs_linux.sh        # Linux Ubuntu launcher script
├── run_gcs_windows.bat     # Windows desktop launcher script
├── requirements.txt        # Python dependency specifications
└── README.md               # System documentation & quickstart
```

---

## 👥 Authors
- **Sheldon** — GCS Architecture & Mission Systems (`sheldon` branch)
- **Mukil** — Lead & System Integration
- **TEAM EDITH**
