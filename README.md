# 🛸 TEAM EDITH | AirMouse Ground Control Station (GCS)
**Autonomous GPS-Denied Indoor Search, Mapping & Survivor Localization Challenge**  
*NIDAR AirMouse Challenge — Track 1 (PS2)*  
*Built with ArduPilot DDS (Micro-XRCE-DDS) & ROS 2 Architecture*

---

## 📌 Overview
The **TEAM EDITH AirMouse Ground Control Station (GCS)** is an aerospace-grade, high-performance tactical monitoring station designed for autonomous drones operating in GPS-denied indoor disaster corridors.

Driven natively by **ArduPilot DDS (Micro-XRCE-DDS)** and standard **ROS 2 interfaces**, every widget and telemetry readout directly reflects real drone topic states.

---

## 🛰️ ArduPilot ROS 2 DDS Interface Architecture

| Telemetry / Function | ROS 2 Topic Name | Message Type (`msg`) | Key Data Fields |
|---|---|---|---|
| **Battery Power & Health** | `/ap/battery` | `sensor_msgs/msg/BatteryState` | `voltage` (12.6V), `percentage` (1.00), `charge` (3.30Ah), `current`, `power_supply_status` |
| **Drone Pose & SLAM** | `/ap/pose/filtered` | `geometry_msgs/msg/PoseStamped` | `pose.position.x`, `pose.position.y`, `pose.position.z`, orientation quaternion |
| **Ground Velocity** | `/ap/twist/filtered` | `geometry_msgs/msg/TwistStamped` | `twist.linear.x`, `twist.linear.y`, `twist.linear.z` |
| **Avionics & IMU** | `/ap/imu/experimental/data`| `sensor_msgs/msg/Imu` | `linear_acceleration`, `angular_velocity`, orientation |
| **Navigation & Sat Fix** | `/ap/navsat` | `sensor_msgs/msg/NavSatFix` | `latitude`, `longitude`, `altitude`, `status` |
| **Flight Control Commands**| `/ap/cmd_vel` | `geometry_msgs/msg/Twist` | Autonomous velocity & navigation commands |
| **LiDAR 360° Scan** | `/scan` | `sensor_msgs/msg/LaserScan` | 360° point cloud range data for Cartographer SLAM |
| **Vision Camera Feed** | `/camera/image_raw` | `sensor_msgs/msg/Image` | 30 FPS RGB / Thermal stream with YOLOv8 inference |

---

## 🌟 Key Features

1. **Clean & Uncluttered Aerospace Layout:**
   - Spacious 2-column interface designed specifically to eliminate visual clutter.
   - Dedicated **ROS 2 DDS Live Topics Ribbon** showing active topics and update frequencies at a glance.
2. **2D Robotic SLAM Canvas:**
   - Cartographer occupancy grid, dynamic costmap inflation layer, 1m discrete metric grid (A–P, 1–15).
   - Real-time rotating 360° LiDAR cone and flight trajectory path.
3. **Survivor Localization Matrix (T1–T6):**
   - Autonomous detection tracking with 1m x 1m grid tags, confidence ratings, and acoustic sonar alerts.
4. **Interactive ROS 2 Topic Echo Terminal:**
   - Single-click terminal modal displaying raw YAML streams identical to `ros2 topic echo /ap/battery`.
5. **Safety Controls:**
   - One-click `START AUTONOMOUS SEARCH`, `HOLD / HOVER`, and `EMERGENCY ABORT (RTL)` back to Entry LZ `[B-4]`.

---

## 🚀 Quick Start

### 🐧 Running on Linux (Ubuntu 22.04 / 24.04 LTS with ROS 2 Humble/Iron/Jazzy)
Ensure Python 3 and Tkinter are available:
```bash
sudo apt update
sudo apt install -y python3 python3-tk
```
Run the application (automatically attaches to active ROS 2 environment):
```bash
python3 airmouse_gcs.py
```

### 🪟 Running on Windows
Simply run:
```cmd
python airmouse_gcs.py
```
*Or double-click:* `run_gcs_windows.bat`

*(Note: On Windows without native ROS 2 installed, the built-in high-fidelity ArduPilot DDS topic emulator automatically runs to provide an identical testing experience).*

---

## 👥 Authors
- **Sheldon** — GCS Architecture & Mission Systems (`sheldon` branch)
- **Mukil** — Lead & System Integration
- **TEAM EDITH**
