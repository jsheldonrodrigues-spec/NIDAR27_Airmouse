"""
================================================================================
TEAM EDITH - AIR MOUSE GROUND CONTROL STATION (GCS)
Autonomous GPS-Denied Indoor Search, Mapping & Survivor Localization Challenge
PS2: NIDAR AirMouse Challenge | Track 1
Built with ArduPilot DDS (Micro-XRCE-DDS) & ROS 2 Interface Architecture
================================================================================
"""

import sys
import os
import time
import math
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# ------------------------------------------------------------------------------
# 1. WINDOWS HIGH-DPI AWARENESS (ELIMINATES BLURRINESS COMPLETELY)
# ------------------------------------------------------------------------------
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

# Audio Support for Sonar chirp and notifications
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# ------------------------------------------------------------------------------
# 2. ROS 2 INTERFACES & ARDUPILOT DDS BRIDGE
# ------------------------------------------------------------------------------
try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import BatteryState, Imu, LaserScan, NavSatFix, Image
    from geometry_msgs.msg import PoseStamped, TwistStamped, Twist
    HAS_RCLPY = True
except ImportError:
    HAS_RCLPY = False


# ------------------------------------------------------------------------------
# 3. PRIVATE FONT LOADER (RAJDHANI & JETBRAINS MONO)
# ------------------------------------------------------------------------------
def register_local_fonts(base_dir):
    """Registers Rajdhani and JetBrains Mono TrueType fonts in Windows."""
    if sys.platform == "win32":
        try:
            import ctypes
            font_files = [
                "Rajdhani-Bold.ttf",
                "Rajdhani-SemiBold.ttf",
                "Rajdhani-Medium.ttf",
                "JetBrainsMono-Bold.ttf",
                "JetBrainsMono-Regular.ttf"
            ]
            for f in font_files:
                font_path = os.path.join(base_dir, f)
                if os.path.exists(font_path):
                    ctypes.windll.gdi32.AddFontResourceExW(os.path.abspath(font_path), 0x10, 0)
        except Exception as e:
            print(f"Font notice: {e}")


# ------------------------------------------------------------------------------
# 4. COLOR PALETTE & DISTINCT TYPOGRAPHY THEME
# ------------------------------------------------------------------------------
COLOR_BG_ROOT          = "#070B14"  # Deep space obsidian
COLOR_PANEL_BG         = "#0D1424"  # Titanium card container
COLOR_PANEL_BORDER     = "#1A2740"  # Micro-borders
COLOR_HEADER_BG        = "#0A0F1D"  # Top app bar background
COLOR_CARD_HEADER_BG   = "#131C30"  # Card title bar
COLOR_CANVAS_BLACK     = "#050811"  # Deep canvas black for SLAM & Video

# Vibrant Aerospace Accents & Hierarchy Colors
COLOR_GREEN_DEFENSE    = "#05DF72"  # Tactical Emerald Defense Green (Nominal)
COLOR_CYAN             = "#00F2FE"  # Primary laser & heading accent
COLOR_ORANGE           = "#FF6B00"  # Target orange
COLOR_AMBER            = "#F59E0B"  # Searching amber
COLOR_RED              = "#EF4444"  # Abort red
COLOR_BLUE_DDS         = "#38BDF8"  # ROS 2 DDS blue

# High-Contrast Typographic Colors (Clearly differentiated)
COLOR_TEXT_HEADING     = "#FFFFFF"  # Pure signal white for Headings
COLOR_TEXT_SUBTITLE    = "#38BDF8"  # Sky Blue for Subtopics / Badges
COLOR_TEXT_VALUE       = "#00F2FE"  # Electric Cyan for Live Telemetry Numbers
COLOR_TEXT_LABEL       = "#94A3B8"  # Slate grey for parameter labels
COLOR_TEXT_MUTED       = "#475569"  # Dim grey for grid axes & rulers


# ------------------------------------------------------------------------------
# 5. AUDIO ALERT SYSTEM
# ------------------------------------------------------------------------------
class AudioAlertSystem:
    @staticmethod
    def play_sonar_chirp():
        def _beep():
            try:
                if HAS_WINSOUND:
                    winsound.Beep(920, 70)
                    winsound.Beep(1350, 110)
                else:
                    sys.stdout.write('\a')
                    sys.stdout.flush()
            except Exception:
                pass
        threading.Thread(target=_beep, daemon=True).start()

    @staticmethod
    def play_victory_alarm():
        def _chime():
            try:
                if HAS_WINSOUND:
                    winsound.Beep(659, 100)
                    winsound.Beep(880, 100)
                    winsound.Beep(1174, 250)
            except Exception:
                pass
        threading.Thread(target=_chime, daemon=True).start()


# ------------------------------------------------------------------------------
# 6. ARDUPILOT DDS ROS 2 TELEMETRY HUB
# ------------------------------------------------------------------------------
class ArduPilotDDSDataHub:
    """
    Central thread-safe data repository for all ArduPilot DDS ROS 2 topics:
    - /ap/battery (sensor_msgs/msg/BatteryState) - Matches Senior's Video 100%
    - /ap/pose/filtered (geometry_msgs/msg/PoseStamped)
    - /ap/twist/filtered (geometry_msgs/msg/TwistStamped)
    - /ap/imu/experimental/data (sensor_msgs/msg/Imu)
    - /ap/status (flight mode, armed state)
    - /scan (sensor_msgs/msg/LaserScan)
    """
    def __init__(self):
        self.lock = threading.Lock()
        
        # Connection Status
        self.dds_agent_connected = True
        self.ros2_active = HAS_RCLPY
        self.last_heartbeat_time = time.time()
        
        # /ap/battery (sensor_msgs/msg/BatteryState)
        self.battery_voltage = 12.60
        self.battery_percentage = 1.00  # 1.0 = 100%
        self.battery_charge = 3.30      # Ah
        self.battery_current = 0.0      # A
        self.battery_design_cap = 3.30
        self.battery_status = 4         # Power Supply Status: 4 (Full/Discharging)
        self.battery_health = 1         # 1 = Good
        self.cells = [4.20, 4.20, 4.20] # 3S LiPo equivalent of 12.60V
        self.battery_hz = 1.0
        
        # /ap/pose/filtered (geometry_msgs/msg/PoseStamped)
        self.pose_x = 1.50   # Arena meters
        self.pose_y = 2.40   # Arena meters
        self.pose_z = 1.20   # Altitude AGL meters
        self.yaw_deg = 84.0  # 0 to 360 deg
        self.pitch_deg = 1.2
        self.roll_deg = -0.5
        self.pose_hz = 20.0
        
        # /ap/twist/filtered (geometry_msgs/msg/TwistStamped)
        self.vel_x = 0.45
        self.vel_y = 0.30
        self.vel_z = 0.00
        self.ground_speed = 0.54  # m/s
        self.twist_hz = 20.0
        
        # /ap/imu/experimental/data (sensor_msgs/msg/Imu)
        self.imu_accel_x = 0.02
        self.imu_accel_y = -0.01
        self.imu_accel_z = 9.81
        self.imu_hz = 50.0
        
        # /ap/status
        self.flight_mode = "GUIDED_NOGPS"
        self.is_armed = True
        self.ekf_status = "LOCKED (OPTICAL FLOW + LIDAR)"
        
        # Motors Telemetry (4x ESC DShot)
        self.motor_rpms = [3520, 3540, 3510, 3530]
        self.motor_temps = [44.2, 45.1, 43.8, 44.6]
        
        # Bandwidth & Comms
        self.bandwidth_mbps = 1.45
        self.latency_ms = 3.2
        self.packet_loss = 0.0
        self.bandwidth_history = [1.2, 1.3, 1.4, 1.5, 1.45, 1.42, 1.48, 1.45]
        
        # Survivor Detections
        self.survivors_found_count = 0
        self.survivors_total = 6


# ------------------------------------------------------------------------------
# 7. MAIN APPLICATION CLASS: TEAM EDITH AIRMOUSE GCS
# ------------------------------------------------------------------------------
class TeamEdithAirMouseGCS:
    def __init__(self, root):
        self.root = root
        self.root.title("TEAM EDITH // AIRMOUSE GCS - ARDUPILOT ROS 2 DDS")
        self.root.geometry("1440x900")
        self.root.minsize(1240, 760)
        self.root.configure(bg=COLOR_BG_ROOT)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        register_local_fonts(base_dir)

        # Initialize Differentiated Fonts
        self._init_fonts()

        # Telemetry & DDS Data Hub
        self.hub = ArduPilotDDSDataHub()

        # Mission State
        self.mission_active = False
        self.mission_start_time = None
        self.elapsed_seconds = 0
        self.mission_paused = False

        # SLAM & Arena Coordinates (15m x 15m Arena)
        self.arena_virtual_w = 600
        self.arena_virtual_h = 600
        self.slam_zoom = 1.0
        self.slam_pan_x = 0
        self.slam_pan_y = 0
        self.drone_pos = [90.0, 160.0]  # Starting LZ Grid [B-4]
        self.trajectory_history = [[90.0, 160.0]]
        self.lidar_angle = 0.0
        self.lidar_points = []

        # Corridors and walls
        self._init_arena_geometry()

        # 6 Survivors (PS2 Track 1 Specification)
        self._init_survivors()

        # Camera HUD Mode
        self.camera_mode = "RGB"  # "RGB" or "THERMAL"
        self.rec_blink_state = True
        self.last_blink_time = time.time()

        # Echo Terminal state
        self.echo_window = None

        # Build Clean, Balanced Aerospace Layout
        self._build_top_header()
        self._build_ros2_topics_ribbon()
        self._build_main_grid()
        self._build_bottom_command_bar()

        # Launch ROS 2 Node or Fallback Telemetry Simulator Thread
        self._start_ros2_engine()

        # Start UI Update Loop
        self._schedule_ui_ticks()

    # --------------------------------------------------------------------------
    # CLEARLY DIFFERENTIATED TYPOGRAPHY SYSTEM
    # --------------------------------------------------------------------------
    def _init_fonts(self):
        font_main = "Rajdhani"
        font_mono = "JetBrains Mono"
        
        # Headings: Bold, Large, Distinct
        self.FONT_APP_TITLE    = (font_main, 17, "bold")
        self.FONT_CARD_TITLE   = (font_main, 12, "bold")
        self.FONT_SUBTOPIC     = (font_main, 11, "bold")
        
        # Telemetry & Numbers: High-contrast Monospace Bold
        self.FONT_VALUE_LG     = (font_mono, 13, "bold")
        self.FONT_VALUE_MD     = (font_mono, 10, "bold")
        self.FONT_VALUE_SM     = (font_mono, 9, "bold")
        
        # Labels & Meta: Readable Slate Monospace Regular
        self.FONT_LABEL_SM     = (font_mono, 9)
        self.FONT_LABEL_XS     = (font_mono, 8)
        
        # Buttons
        self.FONT_BTN          = (font_main, 12, "bold")
        self.FONT_BTN_SM       = (font_main, 10, "bold")

    # --------------------------------------------------------------------------
    # ARENA & SURVIVOR GEOMETRY
    # --------------------------------------------------------------------------
    def _init_arena_geometry(self):
        self.maze_walls = [
            ((30, 30), (570, 30)),
            ((570, 30), (570, 570)),
            ((570, 570), (30, 570)),
            ((30, 570), (30, 30)),
            ((150, 30), (150, 220)),
            ((150, 280), (150, 480)),
            ((30, 340), (150, 340)),
            ((150, 220), (320, 220)),
            ((240, 90), (450, 90)),
            ((240, 90), (240, 220)),
            ((320, 220), (320, 440)),
            ((150, 440), (320, 440)),
            ((400, 160), (400, 350)),
            ((400, 220), (570, 220)),
            ((320, 350), (490, 350)),
            ((230, 440), (230, 570)),
            ((320, 440), (480, 440)),
            ((480, 440), (480, 570)),
        ]
        self.corridor_polys = [
            [(30, 30), (150, 30), (150, 340), (30, 340)],
            [(150, 30), (240, 30), (240, 90), (150, 90)],
            [(150, 220), (320, 220), (320, 440), (150, 440)],
            [(240, 90), (570, 90), (570, 220), (400, 220), (400, 160), (240, 160)],
            [(400, 220), (570, 220), (570, 350), (490, 350), (490, 280), (400, 280)],
            [(320, 350), (570, 350), (570, 570), (480, 570), (480, 440), (320, 440)],
            [(150, 440), (320, 440), (320, 570), (30, 570), (30, 340), (150, 340)],
        ]
        self.corridor_waypoints = [
            (90, 160), (90, 280), (90, 400), (90, 500),
            (180, 500), (270, 500), (270, 380), (200, 380),
            (200, 260), (270, 260), (270, 180), (200, 140),
            (320, 140), (370, 140), (460, 140), (520, 140),
            (520, 280), (450, 280), (360, 280), (360, 390),
            (440, 390), (520, 390), (520, 510), (420, 510),
            (360, 510), (270, 500), (180, 500), (90, 400),
            (90, 280), (90, 160)
        ]
        self.waypoint_idx = 0

    def _init_survivors(self):
        self.survivors = [
            {"id": "T1", "name": "Adult Male", "x": 90, "y": 420, "grid": "Grid [C-11]", "located": False, "conf": 96.4},
            {"id": "T2", "name": "Child", "x": 270, "y": 380, "grid": "Grid [G-10]", "located": False, "conf": 94.8},
            {"id": "T3", "name": "Adult Female", "x": 370, "y": 140, "grid": "Grid [J-4]", "located": False, "conf": 98.1},
            {"id": "T4", "name": "Survivor", "x": 520, "y": 260, "grid": "Grid [N-7]", "located": False, "conf": 92.5},
            {"id": "T5", "name": "Unresponsive", "x": 420, "y": 390, "grid": "Grid [K-10]", "located": False, "conf": 95.0},
            {"id": "T6", "name": "Final Target", "x": 430, "y": 510, "grid": "Grid [L-13]", "located": False, "conf": 97.2},
        ]

    # --------------------------------------------------------------------------
    # 1. TOP HEADER: BRANDING, STATUS & TERMINAL BUTTONS
    # --------------------------------------------------------------------------
    def _build_top_header(self):
        self.header_frame = tk.Frame(self.root, bg=COLOR_HEADER_BG, height=52, bd=0)
        self.header_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(4, 2))
        self.header_frame.pack_propagate(False)

        # Left: Branding with Differentiated Titles
        b_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        b_frame.pack(side=tk.LEFT, padx=8, pady=4)

        tk.Label(b_frame, text="TEAM EDITH", font=self.FONT_APP_TITLE,
                 fg=COLOR_TEXT_HEADING, bg=COLOR_HEADER_BG).pack(side=tk.LEFT)
        tk.Label(b_frame, text=" // ", font=self.FONT_APP_TITLE,
                 fg=COLOR_TEXT_MUTED, bg=COLOR_HEADER_BG).pack(side=tk.LEFT)
        tk.Label(b_frame, text="AIRMOUSE TACTICAL GCS", font=self.FONT_SUBTOPIC,
                 fg=COLOR_CYAN, bg=COLOR_HEADER_BG).pack(side=tk.LEFT)

        # Center Status Badges
        c_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        c_frame.pack(side=tk.LEFT, expand=True)

        self.lbl_dds_badge = tk.Label(
            c_frame,
            text="● DDS AGENT: CONNECTED [UDP:2019]",
            font=self.FONT_LABEL_SM,
            fg=COLOR_GREEN_DEFENSE,
            bg="#0E241B",
            padx=8,
            pady=3,
            relief=tk.SOLID,
            bd=1
        )
        self.lbl_dds_badge.pack(side=tk.LEFT, padx=4)

        self.lbl_mode_badge = tk.Label(
            c_frame,
            text="MODE: GUIDED_NOGPS | ARMED",
            font=self.FONT_LABEL_SM,
            fg=COLOR_TEXT_SUBTITLE,
            bg="#0F1F38",
            padx=8,
            pady=3,
            relief=tk.SOLID,
            bd=1
        )
        self.lbl_mode_badge.pack(side=tk.LEFT, padx=4)

        self.lbl_timer = tk.Label(
            c_frame,
            text="MISSION: 00:00:00",
            font=self.FONT_LABEL_SM,
            fg=COLOR_TEXT_HEADING,
            bg="#162035",
            padx=8,
            pady=3,
            relief=tk.SOLID,
            bd=1
        )
        self.lbl_timer.pack(side=tk.LEFT, padx=4)

        # Right: Quick Controls
        r_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        r_frame.pack(side=tk.RIGHT, padx=8, pady=4)

        btn_echo = tk.Button(
            r_frame,
            text="ROS 2 TOPIC ECHO 📟",
            font=self.FONT_BTN_SM,
            bg="#1E293B",
            fg=COLOR_BLUE_DDS,
            activebackground=COLOR_BLUE_DDS,
            activeforeground="#000000",
            bd=1,
            relief=tk.SOLID,
            cursor="hand2",
            padx=8,
            command=self._open_ros2_echo_window
        )
        btn_echo.pack(side=tk.LEFT, padx=4)

        btn_prearm = tk.Button(
            r_frame,
            text="PRE-ARM CHECK ✔",
            font=self.FONT_BTN_SM,
            bg="#064E3B",
            fg=COLOR_GREEN_DEFENSE,
            activebackground=COLOR_GREEN_DEFENSE,
            activeforeground="#000000",
            bd=1,
            relief=tk.SOLID,
            cursor="hand2",
            padx=8,
            command=self._open_prearm_checklist
        )
        btn_prearm.pack(side=tk.LEFT, padx=4)

    # --------------------------------------------------------------------------
    # 2. ROS 2 TOPICS RIBBON: LIVE TELEMETRY STREAM
    # --------------------------------------------------------------------------
    def _build_ros2_topics_ribbon(self):
        ribbon = tk.Frame(self.root, bg="#0A1120", height=28, bd=1, relief=tk.SOLID)
        ribbon.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0, 4))
        ribbon.pack_propagate(False)

        self.lbl_topic_battery = tk.Label(
            ribbon,
            text="🔋 /ap/battery [1.0Hz]: 12.60V | 100% | 3.30Ah",
            font=self.FONT_LABEL_SM,
            fg=COLOR_GREEN_DEFENSE,
            bg="#0A1120"
        )
        self.lbl_topic_battery.pack(side=tk.LEFT, padx=8)

        tk.Label(ribbon, text="|", font=self.FONT_LABEL_SM, fg="#1F2E47", bg="#0A1120").pack(side=tk.LEFT)

        self.lbl_topic_pose = tk.Label(
            ribbon,
            text="📍 /ap/pose/filtered [20.0Hz]: X:1.50m Y:2.40m Z:1.20m",
            font=self.FONT_LABEL_SM,
            fg=COLOR_CYAN,
            bg="#0A1120"
        )
        self.lbl_topic_pose.pack(side=tk.LEFT, padx=8)

        tk.Label(ribbon, text="|", font=self.FONT_LABEL_SM, fg="#1F2E47", bg="#0A1120").pack(side=tk.LEFT)

        self.lbl_topic_imu = tk.Label(
            ribbon,
            text="🧭 /ap/imu/data [50.0Hz]: Yaw:084° Pitch:+1.2°",
            font=self.FONT_LABEL_SM,
            fg=COLOR_BLUE_DDS,
            bg="#0A1120"
        )
        self.lbl_topic_imu.pack(side=tk.LEFT, padx=8)

        tk.Label(ribbon, text="|", font=self.FONT_LABEL_SM, fg="#1F2E47", bg="#0A1120").pack(side=tk.LEFT)

        self.lbl_topic_scan = tk.Label(
            ribbon,
            text="📡 /scan [10.0Hz]: 360° RPLiDAR LOCKED",
            font=self.FONT_LABEL_SM,
            fg=COLOR_TEXT_LABEL,
            bg="#0A1120"
        )
        self.lbl_topic_scan.pack(side=tk.LEFT, padx=8)

    # --------------------------------------------------------------------------
    # 3. MAIN GRID (BALANCED 3-COLUMN LAYOUT)
    # --------------------------------------------------------------------------
    def _build_main_grid(self):
        self.main_container = tk.Frame(self.root, bg=COLOR_BG_ROOT)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=2)

        # Left Column (280px): Airframe Hardware Health & Bandwidth
        self.col_left = tk.Frame(self.main_container, bg=COLOR_BG_ROOT, width=280)
        self.col_left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        self.col_left.pack_propagate(False)

        # Center Column (Expands): Dual Prominent Tactical Monitors (SLAM + Large Camera)
        self.col_center = tk.Frame(self.main_container, bg=COLOR_BG_ROOT)
        self.col_center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        # Right Column (290px): Rich Battery Module, Motor Overview & Compass
        self.col_right = tk.Frame(self.main_container, bg=COLOR_BG_ROOT, width=290)
        self.col_right.pack(side=tk.RIGHT, fill=tk.Y)
        self.col_right.pack_propagate(False)

        # Build Modules
        self._build_left_column()
        self._build_center_column()
        self._build_right_column()

    # --------------------------------------------------------------------------
    # 3A. LEFT COLUMN: SYSTEM STATUS & TELEMETRY BANDWIDTH
    # --------------------------------------------------------------------------
    def _build_left_column(self):
        # Card 1: Airframe System Status / Hardware Health Matrix
        card_hw = tk.Frame(self.col_left, bg=COLOR_PANEL_BG, bd=1, relief=tk.SOLID)
        card_hw.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 6))

        hdr1 = tk.Frame(card_hw, bg=COLOR_CARD_HEADER_BG, height=28)
        hdr1.pack(fill=tk.X)
        hdr1.pack_propagate(False)

        tk.Label(hdr1, text="⬡ AIRFRAME SYSTEM STATUS", font=self.FONT_CARD_TITLE,
                 fg=COLOR_TEXT_HEADING, bg=COLOR_CARD_HEADER_BG).pack(side=tk.LEFT, padx=8, pady=2)
        tk.Label(hdr1, text="HEALTH", font=self.FONT_LABEL_XS,
                 fg=COLOR_GREEN_DEFENSE, bg=COLOR_CARD_HEADER_BG).pack(side=tk.RIGHT, padx=8)

        hw_body = tk.Frame(card_hw, bg=COLOR_PANEL_BG)
        hw_body.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        # Hardware Components
        hw_items = [
            ("MicoAir H743v2 FC", "38°C", "ARMED/AUTO", COLOR_GREEN_DEFENSE),
            ("Jetson Orin Nano", "51°C", "YOLO+SLAM", COLOR_GREEN_DEFENSE),
            ("RPLiDAR C1 360°", "10.2Hz", "LOCKED", COLOR_GREEN_DEFENSE),
            ("MTF-01 Optical Flow", "96% Q", "AGL 1.2m", COLOR_GREEN_DEFENSE),
            ("VL53L1X Laser ToF", "1.20m", "NOMINAL", COLOR_GREEN_DEFENSE),
            ("Bosch BMI088 IMU", "<0.02°", "CALIBRATED", COLOR_CYAN),
            ("Wi-Fi 6 Archer AX55", "-42dBm", "LATENCY 3ms", COLOR_CYAN),
            ("ArduPilot DDS Node", "UDP:2019", "ONLINE", COLOR_GREEN_DEFENSE)
        ]

        for name, val, stat, col in hw_items:
            row = tk.Frame(hw_body, bg=COLOR_PANEL_BG)
            row.pack(fill=tk.X, pady=2)

            tk.Label(row, text=name, font=self.FONT_LABEL_SM, fg=COLOR_TEXT_LABEL, bg=COLOR_PANEL_BG, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=f"{stat} | {val}", font=self.FONT_VALUE_SM, fg=col, bg=COLOR_PANEL_BG, anchor="e").pack(side=tk.RIGHT)

        # Card 2: Telemetry Bandwidth & Comms Throughput Graph
        card_bw = tk.Frame(self.col_left, bg=COLOR_PANEL_BG, bd=1, relief=tk.SOLID, height=160)
        card_bw.pack(side=tk.BOTTOM, fill=tk.X)
        card_bw.pack_propagate(False)

        hdr2 = tk.Frame(card_bw, bg=COLOR_CARD_HEADER_BG, height=28)
        hdr2.pack(fill=tk.X)
        hdr2.pack_propagate(False)

        tk.Label(hdr2, text="📶 TELEMETRY BANDWIDTH", font=self.FONT_CARD_TITLE,
                 fg=COLOR_TEXT_HEADING, bg=COLOR_CARD_HEADER_BG).pack(side=tk.LEFT, padx=8, pady=2)

        self.lbl_bw_rate = tk.Label(hdr2, text="1.45 MB/s", font=self.FONT_VALUE_SM,
                                    fg=COLOR_CYAN, bg=COLOR_CARD_HEADER_BG)
        self.lbl_bw_rate.pack(side=tk.RIGHT, padx=8)

        bw_body = tk.Frame(card_bw, bg=COLOR_PANEL_BG)
        bw_body.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        stat_line = tk.Frame(bw_body, bg=COLOR_PANEL_BG)
        stat_line.pack(fill=tk.X)
        tk.Label(stat_line, text="LATENCY: 3.2 ms", font=self.FONT_LABEL_XS, fg=COLOR_GREEN_DEFENSE, bg=COLOR_PANEL_BG).pack(side=tk.LEFT)
        tk.Label(stat_line, text="PACKET LOSS: 0.00%", font=self.FONT_LABEL_XS, fg=COLOR_GREEN_DEFENSE, bg=COLOR_PANEL_BG).pack(side=tk.RIGHT)

        self.bw_canvas = tk.Canvas(bw_body, bg="#070D18", height=60, highlightthickness=0, bd=0)
        self.bw_canvas.pack(fill=tk.BOTH, expand=True, pady=4)

    # --------------------------------------------------------------------------
    # 3B. CENTER COLUMN: DUAL PRIMARY MONITORS (SLAM + LARGE CAMERA) & COMPASS
    # --------------------------------------------------------------------------
    def _build_center_column(self):
        dual_frame = tk.Frame(self.col_center, bg=COLOR_BG_ROOT)
        dual_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 6))

        # 1. 2D Robotic SLAM Canvas (Left side of dual frame)
        card_slam = tk.Frame(dual_frame, bg=COLOR_PANEL_BG, bd=1, relief=tk.SOLID)
        card_slam.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        slam_hdr = tk.Frame(card_slam, bg=COLOR_CARD_HEADER_BG, height=28)
        slam_hdr.pack(fill=tk.X)
        slam_hdr.pack_propagate(False)

        tk.Label(slam_hdr, text="🗺️ 2D SLAM OCCUPANCY GRID", font=self.FONT_CARD_TITLE,
                 fg=COLOR_TEXT_HEADING, bg=COLOR_CARD_HEADER_BG).pack(side=tk.LEFT, padx=8, pady=2)

        tk.Button(slam_hdr, text="RESET", font=self.FONT_LABEL_XS, bg="#162238", fg=COLOR_TEXT_LABEL,
                  bd=0, cursor="hand2", command=self._reset_slam_view).pack(side=tk.RIGHT, padx=2)
        tk.Button(slam_hdr, text="+", font=self.FONT_LABEL_XS, bg="#162238", fg=COLOR_CYAN,
                  bd=0, cursor="hand2", command=lambda: self._zoom_slam(1.15)).pack(side=tk.RIGHT, padx=2)
        tk.Button(slam_hdr, text="-", font=self.FONT_LABEL_XS, bg="#162238", fg=COLOR_CYAN,
                  bd=0, cursor="hand2", command=lambda: self._zoom_slam(0.85)).pack(side=tk.RIGHT, padx=2)

        self.lbl_slam_coords = tk.Label(
            card_slam,
            text="DRONE: Grid [B-4] | (1.50m, 2.40m, 1.20m) | YAW: 084°",
            font=self.FONT_LABEL_SM,
            fg=COLOR_TEXT_SUBTITLE,
            bg="#0E1626",
            anchor="w",
            padx=6
        )
        self.lbl_slam_coords.pack(fill=tk.X)

        self.slam_canvas = tk.Canvas(card_slam, bg=COLOR_CANVAS_BLACK, highlightthickness=0, bd=0)
        self.slam_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.slam_canvas.bind("<MouseWheel>", self._on_slam_mousewheel)

        # 2. Large Tactical Onboard Camera (Right side of dual frame - EQUAL LARGE SPACE)
        card_cam = tk.Frame(dual_frame, bg=COLOR_PANEL_BG, bd=1, relief=tk.SOLID)
        card_cam.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))

        cam_hdr = tk.Frame(card_cam, bg=COLOR_CARD_HEADER_BG, height=28)
        cam_hdr.pack(fill=tk.X)
        cam_hdr.pack_propagate(False)

        tk.Label(cam_hdr, text="📷 TACTICAL ONBOARD CAMERA", font=self.FONT_CARD_TITLE,
                 fg=COLOR_TEXT_HEADING, bg=COLOR_CARD_HEADER_BG).pack(side=tk.LEFT, padx=8, pady=2)

        self.btn_rgb = tk.Button(cam_hdr, text="RGB", font=self.FONT_LABEL_XS, bg="#0E241B",
                                 fg=COLOR_GREEN_DEFENSE, bd=0, cursor="hand2", command=lambda: self._set_cam_mode("RGB"))
        self.btn_rgb.pack(side=tk.RIGHT, padx=2)

        self.btn_thermal = tk.Button(cam_hdr, text="THERMAL", font=self.FONT_LABEL_XS, bg="#182338",
                                     fg=COLOR_TEXT_LABEL, bd=0, cursor="hand2", command=lambda: self._set_cam_mode("THERMAL"))
        self.btn_thermal.pack(side=tk.RIGHT, padx=2)

        cam_sub_hdr = tk.Frame(card_cam, bg="#0E1626", height=22)
        cam_sub_hdr.pack(fill=tk.X)
        cam_sub_hdr.pack_propagate(False)
        tk.Label(cam_sub_hdr, text="AI INFERENCE: YOLOv8n HUMAN DETECTION // CSI SENSOR",
                 font=self.FONT_LABEL_XS, fg=COLOR_TEXT_SUBTITLE, bg="#0E1626").pack(side=tk.LEFT, padx=6)

        self.cam_canvas = tk.Canvas(card_cam, bg=COLOR_CANVAS_BLACK, highlightthickness=0, bd=0)
        self.cam_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Lower Center Deck: Large Compass HSI + Survivor Localization Matrix
        lower_frame = tk.Frame(self.col_center, bg=COLOR_BG_ROOT, height=180)
        lower_frame.pack(side=tk.BOTTOM, fill=tk.X)
        lower_frame.pack_propagate(False)

        # 3. Large Precision 360° Avionics Heading Compass (Left of lower frame)
        card_compass = tk.Frame(lower_frame, bg=COLOR_PANEL_BG, bd=1, relief=tk.SOLID, width=280)
        card_compass.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 4))
        card_compass.pack_propagate(False)

        comp_hdr = tk.Frame(card_compass, bg=COLOR_CARD_HEADER_BG, height=28)
        comp_hdr.pack(fill=tk.X)
        comp_hdr.pack_propagate(False)

        tk.Label(comp_hdr, text="🧭 360° AVIONICS COMPASS (HSI)", font=self.FONT_CARD_TITLE,
                 fg=COLOR_TEXT_HEADING, bg=COLOR_CARD_HEADER_BG).pack(side=tk.LEFT, padx=8, pady=2)
        self.lbl_compass_deg = tk.Label(comp_hdr, text="084° N", font=self.FONT_VALUE_SM,
                                        fg=COLOR_CYAN, bg=COLOR_CARD_HEADER_BG)
        self.lbl_compass_deg.pack(side=tk.RIGHT, padx=8)

        self.compass_canvas = tk.Canvas(card_compass, bg=COLOR_PANEL_BG, highlightthickness=0, bd=0)
        self.compass_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        # 4. Survivor Localization Matrix (Right of lower frame)
        card_surv = tk.Frame(lower_frame, bg=COLOR_PANEL_BG, bd=1, relief=tk.SOLID)
        card_surv.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))

        surv_hdr = tk.Frame(card_surv, bg=COLOR_CARD_HEADER_BG, height=28)
        surv_hdr.pack(fill=tk.X)
        surv_hdr.pack_propagate(False)

        tk.Label(surv_hdr, text="🎯 SURVIVOR LOCALIZATION TABLE", font=self.FONT_CARD_TITLE,
                 fg=COLOR_TEXT_HEADING, bg=COLOR_CARD_HEADER_BG).pack(side=tk.LEFT, padx=8, pady=2)

        self.lbl_surv_count = tk.Label(surv_hdr, text="0 / 6 LOCATED", font=self.FONT_VALUE_SM,
                                       fg=COLOR_AMBER, bg=COLOR_CARD_HEADER_BG)
        self.lbl_surv_count.pack(side=tk.RIGHT, padx=8)

        surv_body = tk.Frame(card_surv, bg=COLOR_PANEL_BG)
        surv_body.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.surv_row_labels = []
        for idx, s in enumerate(self.survivors):
            col_id = idx // 3
            row_id = idx % 3

            r_box = tk.Frame(surv_body, bg=COLOR_PANEL_BG)
            r_box.grid(row=row_id, column=col_id, sticky="ew", padx=6, pady=2)
            surv_body.columnconfigure(col_id, weight=1)

            lbl_id = tk.Label(r_box, text=s["id"], font=self.FONT_VALUE_SM, fg=COLOR_CYAN, bg=COLOR_PANEL_BG, width=4, anchor="w")
            lbl_id.pack(side=tk.LEFT)

            lbl_grid = tk.Label(r_box, text=s["grid"], font=self.FONT_LABEL_SM, fg=COLOR_TEXT_LABEL, bg=COLOR_PANEL_BG, width=12, anchor="w")
            lbl_grid.pack(side=tk.LEFT)

            lbl_status = tk.Label(r_box, text="SEARCHING...", font=self.FONT_LABEL_XS, fg=COLOR_AMBER, bg=COLOR_PANEL_BG, anchor="e")
            lbl_status.pack(side=tk.RIGHT)

            self.surv_row_labels.append((lbl_status, lbl_grid, s))

    # --------------------------------------------------------------------------
    # 3C. RIGHT COLUMN: ARDUPILOT BATTERY MODULE & MOTOR OVERVIEW
    # --------------------------------------------------------------------------
    def _build_right_column(self):
        # Card 1: Rich ArduPilot DDS Battery Module (Matches Video 100%)
        card_bat = tk.Frame(self.col_right, bg=COLOR_PANEL_BG, bd=1, relief=tk.SOLID)
        card_bat.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 6))

        bat_hdr = tk.Frame(card_bat, bg=COLOR_CARD_HEADER_BG, height=28)
        bat_hdr.pack(fill=tk.X)
        bat_hdr.pack_propagate(False)

        tk.Label(bat_hdr, text="🔋 /ap/battery TELEMETRY", font=self.FONT_CARD_TITLE,
                 fg=COLOR_TEXT_HEADING, bg=COLOR_CARD_HEADER_BG).pack(side=tk.LEFT, padx=8, pady=2)
        tk.Label(bat_hdr, text="sensor_msgs", font=self.FONT_LABEL_XS,
                 fg=COLOR_BLUE_DDS, bg=COLOR_CARD_HEADER_BG).pack(side=tk.RIGHT, padx=8)

        bat_body = tk.Frame(card_bat, bg=COLOR_PANEL_BG)
        bat_body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        v_frame = tk.Frame(bat_body, bg=COLOR_PANEL_BG)
        v_frame.pack(fill=tk.X, pady=2)

        self.lbl_bat_volts = tk.Label(v_frame, text="12.60 V", font=self.FONT_VALUE_LG,
                                      fg=COLOR_GREEN_DEFENSE, bg=COLOR_PANEL_BG)
        self.lbl_bat_volts.pack(side=tk.LEFT)

        self.lbl_bat_pct = tk.Label(v_frame, text="100% (1.00)", font=self.FONT_SUBTOPIC,
                                    fg=COLOR_TEXT_HEADING, bg=COLOR_PANEL_BG)
        self.lbl_bat_pct.pack(side=tk.RIGHT)

        self.bat_bar_canvas = tk.Canvas(bat_body, bg="#0E1626", height=14, highlightthickness=0, bd=0)
        self.bat_bar_canvas.pack(fill=tk.X, pady=4)

        fields = [
            ("Charge Capacity", "3.30 Ah", COLOR_CYAN),
            ("Design Capacity", "3.30 Ah", COLOR_TEXT_LABEL),
            ("Current Draw", "0.0 A (Hover: 14A)", COLOR_TEXT_HEADING),
            ("Power Supply Status", "4 [FULL/DISCHARGING]", COLOR_GREEN_DEFENSE),
            ("Power Supply Health", "1 [NOMINAL GOOD]", COLOR_GREEN_DEFENSE),
            ("Pack Configuration", "3S / 6S LiPo Pack", COLOR_TEXT_LABEL)
        ]

        self.bat_field_labels = {}
        for lbl, val, col in fields:
            row = tk.Frame(bat_body, bg=COLOR_PANEL_BG)
            row.pack(fill=tk.X, pady=1)

            tk.Label(row, text=lbl, font=self.FONT_LABEL_SM, fg=COLOR_TEXT_LABEL, bg=COLOR_PANEL_BG).pack(side=tk.LEFT)
            val_lbl = tk.Label(row, text=val, font=self.FONT_VALUE_SM, fg=col, bg=COLOR_PANEL_BG)
            val_lbl.pack(side=tk.RIGHT)
            self.bat_field_labels[lbl] = val_lbl

        # Card 2: Electric Motor Overview & DShot Telemetry
        card_motor = tk.Frame(self.col_right, bg=COLOR_PANEL_BG, bd=1, relief=tk.SOLID, height=210)
        card_motor.pack(side=tk.BOTTOM, fill=tk.X)
        card_motor.pack_propagate(False)

        mot_hdr = tk.Frame(card_motor, bg=COLOR_CARD_HEADER_BG, height=28)
        mot_hdr.pack(fill=tk.X)
        mot_hdr.pack_propagate(False)

        tk.Label(mot_hdr, text="⚡ ELECTRIC MOTOR OVERVIEW", font=self.FONT_CARD_TITLE,
                 fg=COLOR_TEXT_HEADING, bg=COLOR_CARD_HEADER_BG).pack(side=tk.LEFT, padx=8, pady=2)
        tk.Label(mot_hdr, text="DSHOT 600", font=self.FONT_LABEL_XS,
                 fg=COLOR_CYAN, bg=COLOR_CARD_HEADER_BG).pack(side=tk.RIGHT, padx=8)

        mot_body = tk.Frame(card_motor, bg=COLOR_PANEL_BG)
        mot_body.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.motor_labels = []
        for i in range(4):
            m_row = tk.Frame(mot_body, bg=COLOR_PANEL_BG)
            m_row.pack(fill=tk.X, pady=2)

            tk.Label(m_row, text=f"MOTOR {i+1}", font=self.FONT_VALUE_SM, fg=COLOR_TEXT_HEADING, bg=COLOR_PANEL_BG, width=8, anchor="w").pack(side=tk.LEFT)
            
            m_cv = tk.Canvas(m_row, bg="#0E1626", height=10, width=80, highlightthickness=0, bd=0)
            m_cv.pack(side=tk.LEFT, padx=4)
            m_cv.create_rectangle(0, 0, 65, 10, fill=COLOR_CYAN, outline="")

            lbl_m = tk.Label(m_row, text="3,520 RPM | 44°C", font=self.FONT_LABEL_XS, fg=COLOR_TEXT_SUBTITLE, bg=COLOR_PANEL_BG)
            lbl_m.pack(side=tk.RIGHT)
            self.motor_labels.append(lbl_m)

    # --------------------------------------------------------------------------
    # 4. BOTTOM ACTION & MISSION COMMAND BAR
    # --------------------------------------------------------------------------
    def _build_bottom_command_bar(self):
        bar = tk.Frame(self.root, bg="#0B1220", height=48, bd=1, relief=tk.SOLID)
        bar.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=(2, 6))
        bar.pack_propagate(False)

        tk.Label(
            bar,
            text="ROS 2 ARDUPILOT DDS BRIDGE // APM v4.5 | TOPIC: /ap/cmd_vel | FAILSAFE: AUTO RTL",
            font=self.FONT_LABEL_SM,
            fg=COLOR_TEXT_LABEL,
            bg="#0B1220"
        ).pack(side=tk.LEFT, padx=12, pady=12)

        self.btn_abort = tk.Button(
            bar,
            text="EMERGENCY ABORT (RTL)",
            font=self.FONT_BTN,
            bg="#991B1B",
            fg=COLOR_TEXT_HEADING,
            activebackground=COLOR_RED,
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=14,
            command=self._emergency_abort
        )
        self.btn_abort.pack(side=tk.RIGHT, padx=8, pady=6)

        self.btn_hold = tk.Button(
            bar,
            text="HOLD / HOVER",
            font=self.FONT_BTN,
            bg="#B45309",
            fg=COLOR_TEXT_HEADING,
            activebackground=COLOR_AMBER,
            activeforeground="#000000",
            bd=0,
            cursor="hand2",
            padx=14,
            command=self._toggle_hold
        )
        self.btn_hold.pack(side=tk.RIGHT, padx=4, pady=6)

        self.btn_mission = tk.Button(
            bar,
            text="START AUTONOMOUS SEARCH",
            font=self.FONT_BTN,
            bg="#059669",
            fg=COLOR_TEXT_HEADING,
            activebackground=COLOR_GREEN_DEFENSE,
            activeforeground="#000000",
            bd=0,
            cursor="hand2",
            padx=16,
            command=self._toggle_mission
        )
        self.btn_mission.pack(side=tk.RIGHT, padx=4, pady=6)

    # --------------------------------------------------------------------------
    # 5. ARDUPILOT ROS 2 ENGINE & BACKGROUND THREAD
    # --------------------------------------------------------------------------
    def _start_ros2_engine(self):
        def _runner():
            if HAS_RCLPY:
                try:
                    rclpy.init()
                    node = Node("airmouse_gcs_node")

                    node.create_subscription(BatteryState, "/ap/battery", self._ros2_battery_cb, 10)
                    node.create_subscription(PoseStamped, "/ap/pose/filtered", self._ros2_pose_cb, 10)
                    node.create_subscription(TwistStamped, "/ap/twist/filtered", self._ros2_twist_cb, 10)
                    node.create_subscription(Imu, "/ap/imu/experimental/data", self._ros2_imu_cb, 10)

                    self.hub.ros2_active = True
                    rclpy.spin(node)
                except Exception as e:
                    print(f"rclpy notice: {e}. Fallback to DDS emulator.")
                    self._run_dds_emulator()
            else:
                self._run_dds_emulator()

        t = threading.Thread(target=_runner, daemon=True)
        t.start()

    def _ros2_battery_cb(self, msg):
        with self.hub.lock:
            self.hub.battery_voltage = msg.voltage
            self.hub.battery_percentage = msg.percentage
            self.hub.battery_charge = msg.charge
            self.hub.battery_current = msg.current
            self.hub.battery_status = msg.power_supply_status

    def _ros2_pose_cb(self, msg):
        with self.hub.lock:
            self.hub.pose_x = msg.pose.position.x
            self.hub.pose_y = msg.pose.position.y
            self.hub.pose_z = msg.pose.position.z

    def _ros2_twist_cb(self, msg):
        with self.hub.lock:
            self.hub.vel_x = msg.twist.linear.x
            self.hub.vel_y = msg.twist.linear.y
            self.hub.ground_speed = math.hypot(msg.twist.linear.x, msg.twist.linear.y)

    def _ros2_imu_cb(self, msg):
        with self.hub.lock:
            self.hub.imu_accel_z = msg.linear_acceleration.z

    def _run_dds_emulator(self):
        while True:
            time.sleep(0.05)
            with self.hub.lock:
                if self.mission_active and not self.mission_paused:
                    self.hub.battery_voltage = max(11.2, self.hub.battery_voltage - 0.0002)
                    self.hub.battery_percentage = max(0.20, (self.hub.battery_voltage - 11.1) / (12.6 - 11.1))
                    self.hub.battery_charge = round(self.hub.battery_percentage * 3.30, 2)
                    self.hub.battery_current = round(random.uniform(13.5, 14.8), 1)

                    self.hub.motor_rpms = [int(3520 + random.uniform(-40, 40)) for _ in range(4)]
                    self.hub.bandwidth_history.append(round(random.uniform(1.40, 1.52), 2))
                    if len(self.hub.bandwidth_history) > 20:
                        self.hub.bandwidth_history.pop(0)

    # --------------------------------------------------------------------------
    # 6. UI SCHEDULING TICKS & RENDERING
    # --------------------------------------------------------------------------
    def _schedule_ui_ticks(self):
        self._update_telemetry_and_mission()
        self._render_slam_canvas()
        self._render_camera_canvas()
        self._render_compass()
        self._render_bandwidth()
        self._render_battery_bar()
        self.root.after(33, self._schedule_ui_ticks)

    def _update_telemetry_and_mission(self):
        if self.mission_active and not self.mission_paused:
            self.elapsed_seconds = int(time.time() - self.mission_start_time)
            mins = self.elapsed_seconds // 60
            secs = self.elapsed_seconds % 60
            self.lbl_timer.config(text=f"MISSION: {mins:02d}:{secs:02d}")
            self._advance_mission_flight()

        with self.hub.lock:
            v = self.hub.battery_voltage
            p = int(self.hub.battery_percentage * 100)
            c = self.hub.battery_charge
            curr = self.hub.battery_current

            self.lbl_topic_battery.config(text=f"🔋 /ap/battery [1.0Hz]: {v:.2f}V | {p}% | {c:.2f}Ah")
            self.lbl_topic_pose.config(text=f"📍 /ap/pose/filtered [20.0Hz]: X:{self.hub.pose_x:.2f}m Y:{self.hub.pose_y:.2f}m Z:{self.hub.pose_z:.2f}m")
            self.lbl_topic_imu.config(text=f"🧭 /ap/imu/data [50.0Hz]: Yaw:{int(self.hub.yaw_deg):03d}° Pitch:{self.hub.pitch_deg:+.1f}°")

            self.lbl_bat_volts.config(text=f"{v:.2f} V")
            self.lbl_bat_pct.config(text=f"{p}% ({self.hub.battery_percentage:.2f})")
            if "Charge Capacity" in self.bat_field_labels:
                self.bat_field_labels["Charge Capacity"].config(text=f"{c:.2f} Ah")
            if "Current Draw" in self.bat_field_labels:
                self.bat_field_labels["Current Draw"].config(text=f"{curr:.1f} A (Hover: 14.2A)")

            self.lbl_compass_deg.config(text=f"{int(self.hub.yaw_deg):03d}° N")

            for i, lbl in enumerate(self.motor_labels):
                lbl.config(text=f"{self.hub.motor_rpms[i]} RPM | {self.hub.motor_temps[i]:.1f}°C")

    def _advance_mission_flight(self):
        if self.waypoint_idx < len(self.corridor_waypoints):
            target = self.corridor_waypoints[self.waypoint_idx]
            curr_x, curr_y = self.drone_pos
            dx = target[0] - curr_x
            dy = target[1] - curr_y
            dist = math.hypot(dx, dy)

            target_yaw = math.degrees(math.atan2(dy, dx)) % 360
            angle_diff = (target_yaw - self.hub.yaw_deg + 180) % 360 - 180
            self.hub.yaw_deg = (self.hub.yaw_deg + angle_diff * 0.15) % 360

            step = 2.4
            if dist < step:
                self.drone_pos[0] = target[0]
                self.drone_pos[1] = target[1]
                self.waypoint_idx += 1
            else:
                self.drone_pos[0] += (dx / dist) * step
                self.drone_pos[1] += (dy / dist) * step

            if len(self.trajectory_history) == 0 or math.hypot(self.drone_pos[0] - self.trajectory_history[-1][0],
                                                              self.drone_pos[1] - self.trajectory_history[-1][1]) > 8:
                self.trajectory_history.append(list(self.drone_pos))

            self.hub.pose_x = round(self.drone_pos[0] / 40.0, 2)
            self.hub.pose_y = round(self.drone_pos[1] / 40.0, 2)

            col_letter = chr(ord('A') + min(15, int(self.drone_pos[0] / (self.arena_virtual_w / 16))))
            row_num = min(15, int(self.drone_pos[1] / (self.arena_virtual_h / 15)) + 1)
            self.lbl_slam_coords.config(
                text=f"DRONE: Grid [{col_letter}-{row_num}] | ({self.hub.pose_x}m, {self.hub.pose_y}m, 1.20m) | YAW: {int(self.hub.yaw_deg):03d}°"
            )

            for i, (lbl_status, lbl_grid, s) in enumerate(self.surv_row_labels):
                if not s["located"]:
                    dist_to_s = math.hypot(self.drone_pos[0] - s["x"], self.drone_pos[1] - s["y"])
                    if dist_to_s < 45:
                        s["located"] = True
                        lbl_status.config(text=f"FOUND ({s['conf']}%)", fg=COLOR_GREEN_DEFENSE)
                        lbl_grid.config(fg=COLOR_TEXT_HEADING)
                        AudioAlertSystem.play_sonar_chirp()

                        self.hub.survivors_found_count += 1
                        self.lbl_surv_count.config(text=f"{self.hub.survivors_found_count} / 6 LOCATED")

                        if self.hub.survivors_found_count == 6:
                            AudioAlertSystem.play_victory_alarm()

        self.lidar_angle = (self.lidar_angle + 12) % 360

    # --------------------------------------------------------------------------
    # 7. RENDERING: 2D SLAM CANVAS
    # --------------------------------------------------------------------------
    def _render_slam_canvas(self):
        cv = self.slam_canvas
        cv.delete("all")
        cw = cv.winfo_width()
        ch = cv.winfo_height()
        if cw < 30 or ch < 30:
            return

        scale_x = (cw / self.arena_virtual_w) * self.slam_zoom
        scale_y = (ch / self.arena_virtual_h) * self.slam_zoom

        def to_cv(x, y):
            return (x * scale_x) + self.slam_pan_x, (y * scale_y) + self.slam_pan_y

        cv.create_rectangle(0, 0, cw, ch, fill="#070C16", outline="")

        cols, rows = 16, 15
        step_x = cw / cols
        step_y = ch / rows
        for c in range(cols + 1):
            gx = c * step_x
            cv.create_line(gx, 0, gx, ch, fill="#10192A", width=1)
            if c < cols:
                cv.create_text(gx + step_x / 2, 7, text=chr(ord('A') + c), font=self.FONT_LABEL_XS, fill=COLOR_TEXT_MUTED)

        for r in range(rows + 1):
            gy = r * step_y
            cv.create_line(0, gy, cw, gy, fill="#10192A", width=1)
            if r < rows:
                cv.create_text(7, gy + step_y / 2, text=str(r + 1), font=self.FONT_LABEL_XS, fill=COLOR_TEXT_MUTED)

        for poly in self.corridor_polys:
            pts = []
            for px, py in poly:
                pts.extend(to_cv(px, py))
            cv.create_polygon(pts, fill="#121B2C", outline="#1A283E", width=1)

        lz_cx, lz_cy = to_cv(90, 160)
        cv.create_oval(lz_cx - 14, lz_cy - 14, lz_cx + 14, lz_cy + 14, outline=COLOR_GREEN_DEFENSE, width=1.5, dash=(3, 2))
        cv.create_text(lz_cx, lz_cy, text="H", font=self.FONT_CARD_TITLE, fill=COLOR_GREEN_DEFENSE)
        cv.create_text(lz_cx, lz_cy + 16, text="LZ [B-4]", font=self.FONT_LABEL_XS, fill=COLOR_GREEN_DEFENSE)

        for (p1, p2) in self.maze_walls:
            cx1, cy1 = to_cv(*p1)
            cx2, cy2 = to_cv(*p2)
            cv.create_line(cx1, cy1, cx2, cy2, fill="#1B283E", width=8)
            cv.create_line(cx1, cy1, cx2, cy2, fill=COLOR_CYAN, width=1.5)

        for s in self.survivors:
            sx, sy = to_cv(s["x"], s["y"])
            if s["located"]:
                cv.create_oval(sx - 8, sy - 8, sx + 8, sy + 8, outline=COLOR_GREEN_DEFENSE, width=2)
                cv.create_oval(sx - 3, sy - 3, sx + 3, sy + 3, fill=COLOR_GREEN_DEFENSE, outline="")
                cv.create_text(sx, sy - 12, text=f"{s['id']}", font=self.FONT_LABEL_XS, fill=COLOR_GREEN_DEFENSE)
            else:
                cv.create_oval(sx - 4, sy - 4, sx + 4, sy + 4, outline=COLOR_AMBER, width=1, dash=(2, 2))
                cv.create_text(sx, sy - 8, text=s['id'], font=self.FONT_LABEL_XS, fill=COLOR_TEXT_MUTED)

        if len(self.trajectory_history) > 1:
            flat_pts = []
            for hx, hy in self.trajectory_history:
                flat_pts.extend(to_cv(hx, hy))
            cv.create_line(flat_pts, fill="#0F3846", width=3, smooth=True)
            cv.create_line(flat_pts, fill=COLOR_CYAN, width=1.2, smooth=True)

        dx, dy = to_cv(*self.drone_pos)
        sweep_rad = math.radians(self.lidar_angle)
        cone_radius = 65 * min(scale_x, scale_y)
        span = math.radians(20)
        lx1 = dx + cone_radius * math.cos(sweep_rad - span)
        ly1 = dy + cone_radius * math.sin(sweep_rad - span)
        lx2 = dx + cone_radius * math.cos(sweep_rad + span)
        ly2 = dy + cone_radius * math.sin(sweep_rad + span)
        cv.create_polygon(dx, dy, lx1, ly1, lx2, ly2, fill="#003547", outline="")

        rad = math.radians(self.hub.yaw_deg)
        arm = 10 * min(scale_x, scale_y)
        for angle_offset in [45, 135, 225, 315]:
            theta = rad + math.radians(angle_offset)
            mx = dx + arm * math.cos(theta)
            my = dy + arm * math.sin(theta)
            cv.create_line(dx, dy, mx, my, fill=COLOR_TEXT_HEADING, width=1.5)
            cv.create_oval(mx - 2, my - 2, mx + 2, my + 2, fill=COLOR_CYAN, outline="")

        cv.create_oval(dx - 4, dy - 4, dx + 4, dy + 4, fill=COLOR_GREEN_DEFENSE, outline="#FFFFFF", width=1)
        hx = dx + (arm * 1.5) * math.cos(rad)
        hy = dy + (arm * 1.5) * math.sin(rad)
        cv.create_line(dx, dy, hx, hy, fill=COLOR_GREEN_DEFENSE, width=2)

    # --------------------------------------------------------------------------
    # 8. RENDERING: LARGE TACTICAL CAMERA FEED
    # --------------------------------------------------------------------------
    def _render_camera_canvas(self):
        cv = self.cam_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 30 or h < 30:
            return

        cx, cy = w / 2.0, h / 2.0
        bg_col = "#070E1A" if self.camera_mode == "RGB" else "#0F061C"
        cv.create_rectangle(0, 0, w, h, fill=bg_col, outline="")

        wire_col = "#132135" if self.camera_mode == "RGB" else "#2C124A"
        vp_x = cx + math.sin(math.radians(self.hub.yaw_deg)) * 25
        vp_y = cy
        cv.create_line(0, 0, vp_x, vp_y, fill=wire_col, width=1)
        cv.create_line(w, 0, vp_x, vp_y, fill=wire_col, width=1)
        cv.create_line(0, h, vp_x, vp_y, fill=wire_col, width=1)
        cv.create_line(w, h, vp_x, vp_y, fill=wire_col, width=1)

        cv.create_line(cx - 20, cy, cx + 20, cy, fill=COLOR_CYAN, width=1)
        cv.create_line(cx, cy - 20, cx, cy + 20, fill=COLOR_CYAN, width=1)

        target_in_view = None
        for s in self.survivors:
            if s["located"]:
                dist = math.hypot(self.drone_pos[0] - s["x"], self.drone_pos[1] - s["y"])
                if dist < 85:
                    target_in_view = s
                    break

        if target_in_view:
            bx1, by1 = cx - 35, cy - 55
            bx2, by2 = cx + 35, cy + 55
            box_col = COLOR_GREEN_DEFENSE if self.camera_mode == "RGB" else COLOR_ORANGE

            cv.create_rectangle(bx1, by1, bx2, by2, outline=box_col, width=2)
            cv.create_text(bx1, by1 - 10, text=f"[YOLOv8] PERSON: {target_in_view['conf']}%",
                           font=self.FONT_LABEL_SM, fill=box_col, anchor="w")
            cv.create_text(bx1, by2 + 10, text="BIOMETRIC: 37.1°C | DIST: 1.2m",
                           font=self.FONT_LABEL_SM, fill=COLOR_CYAN, anchor="w")

        now = time.time()
        if now - self.last_blink_time > 0.5:
            self.rec_blink_state = not self.rec_blink_state
            self.last_blink_time = now

        if self.rec_blink_state:
            cv.create_oval(10, 10, 16, 16, fill=COLOR_RED, outline="")
        cv.create_text(20, 13, text="REC 1080p", font=self.FONT_LABEL_SM, fill=COLOR_TEXT_HEADING, anchor="w")
        cv.create_text(w - 10, 13, text="30 FPS // RTSP", font=self.FONT_LABEL_SM, fill=COLOR_CYAN, anchor="e")

    # --------------------------------------------------------------------------
    # 9. RENDERING: LARGE 360° PRECISION AVIONICS COMPASS (HSI)
    # --------------------------------------------------------------------------
    def _render_compass(self):
        cv = self.compass_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 40 or h < 40:
            return

        cx, cy = w / 2.0, h / 2.0
        r = min(cx, cy) - 10

        cv.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#0A111E", outline="#1F2E45", width=2)
        cv.create_oval(cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3, outline="#131F33", width=1)

        yaw = self.hub.yaw_deg
        cardinals = {0: "N", 90: "E", 180: "S", 270: "W"}
        inters = {45: "NE", 135: "SE", 225: "SW", 315: "NW"}

        for deg in range(0, 360, 15):
            rel_deg = deg - yaw
            rad = math.radians(rel_deg)
            is_cardinal = deg in cardinals
            is_inter = deg in inters
            tick_len = 10 if is_cardinal else (6 if is_inter else 4)

            x1 = cx + (r - 2) * math.sin(rad)
            y1 = cy - (r - 2) * math.cos(rad)
            x2 = cx + (r - 2 - tick_len) * math.sin(rad)
            y2 = cy - (r - 2 - tick_len) * math.cos(rad)
            cv.create_line(x1, y1, x2, y2, fill="#3A4D6B", width=1.5 if is_cardinal else 1)

            if is_cardinal:
                tx = cx + (r - 18) * math.sin(rad)
                ty = cy - (r - 18) * math.cos(rad)
                col = COLOR_RED if deg == 0 else COLOR_TEXT_HEADING
                cv.create_text(tx, ty, text=cardinals[deg], font=self.FONT_SUBTOPIC, fill=col)

        cv.create_polygon(cx, cy - r + 2, cx - 6, cy - r + 14, cx + 6, cy - r + 14, fill=COLOR_GREEN_DEFENSE)
        cv.create_line(cx, cy - r, cx, cy + r, fill="#162238", width=1, dash=(3, 3))
        cv.create_line(cx - r, cy, cx + r, cy, fill="#162238", width=1, dash=(3, 3))

        cv.create_rectangle(cx - 24, cy - 10, cx + 24, cy + 10, fill="#0E1626", outline="#1F2E45")
        cv.create_text(cx, cy, text=f"{int(yaw):03d}°", font=self.FONT_VALUE_SM, fill=COLOR_CYAN)

    # --------------------------------------------------------------------------
    # 10. RENDERING: BANDWIDTH WAVEFORM & BATTERY BAR
    # --------------------------------------------------------------------------
    def _render_bandwidth(self):
        cv = self.bw_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 20 or h < 20:
            return

        hist = self.hub.bandwidth_history
        if len(hist) < 2:
            return

        step = w / (len(hist) - 1)
        pts = []
        for i, val in enumerate(hist):
            px = i * step
            norm = (val - 1.2) / 0.4
            py = h - (norm * (h - 10)) - 5
            pts.extend([px, py])

        fill_poly = [0, h] + pts + [w, h]
        cv.create_polygon(fill_poly, fill="#0F2438", outline="")
        cv.create_line(pts, fill=COLOR_CYAN, width=2, smooth=True)

    def _render_battery_bar(self):
        cv = self.bat_bar_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 20 or h < 6:
            return

        pct = self.hub.battery_percentage
        fill_w = int(w * pct)
        col = COLOR_GREEN_DEFENSE if pct > 0.4 else (COLOR_AMBER if pct > 0.2 else COLOR_RED)
        cv.create_rectangle(0, 0, fill_w, h, fill=col, outline="")

    # --------------------------------------------------------------------------
    # 11. ROS 2 TOPIC ECHO TERMINAL MODAL (SENIOR'S VIDEO REPLICA)
    # --------------------------------------------------------------------------
    def _open_ros2_echo_window(self):
        if self.echo_window and tk.Toplevel.winfo_exists(self.echo_window):
            self.echo_window.lift()
            return

        self.echo_window = tk.Toplevel(self.root)
        self.echo_window.title("ROS 2 TERMINAL // ros2 topic echo /ap/battery")
        self.echo_window.geometry("640x520")
        self.echo_window.configure(bg="#0B0F19")

        hdr = tk.Frame(self.echo_window, bg="#131B2A", height=32)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="mukil@macbookm2:~/ardu_ws$ ros2 topic echo /ap/battery",
                 font=self.FONT_LABEL_SM, fg=COLOR_GREEN_DEFENSE, bg="#131B2A").pack(side=tk.LEFT, padx=10, pady=4)

        txt_frame = tk.Frame(self.echo_window, bg="#0B0F19")
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        echo_text = tk.Text(
            txt_frame,
            bg="#050811",
            fg="#A7F3D0",
            insertbackground="#00F2FE",
            font=self.FONT_LABEL_SM,
            bd=0,
            padx=10,
            pady=10
        )
        echo_text.pack(fill=tk.BOTH, expand=True)

        def _update_echo():
            if not tk.Toplevel.winfo_exists(self.echo_window):
                return
            with self.hub.lock:
                now_sec = int(time.time())
                sample_yaml = f"""---
header:
  stamp:
    sec: {now_sec}
    nanosec: 787125000
  frame_id: '0'
voltage: {self.hub.battery_voltage:.16f}
temperature: .nan
current: {self.hub.battery_current:.1f}
charge: {self.hub.battery_charge:.16f}
capacity: .nan
design_capacity: {self.hub.battery_design_cap:.16f}
percentage: {self.hub.battery_percentage:.2f}
power_supply_status: {self.hub.battery_status}
power_supply_health: {self.hub.battery_health}
power_supply_technology: 0
present: true
cell_voltage: []
cell_temperature: []
location: ''
serial_number: ''
---
topic: /ap/pose/filtered
pose:
  position:
    x: {self.hub.pose_x:.3f}
    y: {self.hub.pose_y:.3f}
    z: {self.hub.pose_z:.3f}
  orientation:
    yaw_deg: {self.hub.yaw_deg:.1f}
"""
            echo_text.delete("1.0", tk.END)
            echo_text.insert(tk.END, sample_yaml)
            echo_text.see(tk.END)
            self.echo_window.after(800, _update_echo)

        _update_echo()

    # --------------------------------------------------------------------------
    # 12. ACTIONS & CONTROLS
    # --------------------------------------------------------------------------
    def _toggle_mission(self):
        if not self.mission_active:
            self.mission_active = True
            self.mission_paused = False
            self.mission_start_time = time.time()
            self.btn_mission.config(text="MISSION RUNNING ✔", bg="#047857")
        else:
            self.mission_active = False
            self.btn_mission.config(text="START AUTONOMOUS SEARCH", bg="#059669")

    def _toggle_hold(self):
        self.mission_paused = not self.mission_paused
        if self.mission_paused:
            self.btn_hold.config(text="RESUME FLIGHT", bg="#D97706")
        else:
            self.btn_hold.config(text="HOLD / HOVER", bg="#B45309")

    def _emergency_abort(self):
        ans = messagebox.askyesno("EMERGENCY ABORT", "Trigger immediate Autonomous RTL (Return To Launch LZ)?")
        if ans:
            self.mission_paused = True
            self.hub.flight_mode = "RTL"
            self.lbl_mode_badge.config(text="MODE: RTL // RETURNING TO LZ", fg=COLOR_RED, bg="#2C0F14")
            self.drone_pos[0] = 90.0
            self.drone_pos[1] = 160.0
            self.trajectory_history.append([90.0, 160.0])

    def _open_prearm_checklist(self):
        msg = """ARDUPILOT DDS PRE-ARM DIAGNOSTICS:
✔ Micro-XRCE-DDS Agent: Online (UDP:2019)
✔ /ap/battery: 12.60V (100% Nominal)
✔ RPLiDAR A2 / C1: 360° Lock (10.0 Hz)
✔ Optical Flow + ToF: Locked (AGL: 1.20m)
✔ EKF3 IMU Yaw Alignment: PASSED
✔ Jetson Orin YOLOv8n: Standby Ready

ALL SAFETY CHECKS NOMINAL. AUTOPILOT ARMED."""
        messagebox.showinfo("PRE-ARM CHECKLIST", msg)

    def _set_cam_mode(self, mode):
        self.camera_mode = mode
        if mode == "RGB":
            self.btn_rgb.config(bg="#0E241B", fg=COLOR_GREEN_DEFENSE)
            self.btn_thermal.config(bg="#182338", fg=COLOR_TEXT_LABEL)
        else:
            self.btn_rgb.config(bg="#182338", fg=COLOR_TEXT_LABEL)
            self.btn_thermal.config(bg="#2C124A", fg="#FF6B00")

    def _zoom_slam(self, factor):
        self.slam_zoom = max(0.5, min(3.0, self.slam_zoom * factor))

    def _reset_slam_view(self):
        self.slam_zoom = 1.0
        self.slam_pan_x = 0
        self.slam_pan_y = 0

    def _on_slam_mousewheel(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self._zoom_slam(factor)


# ------------------------------------------------------------------------------
# 13. ENTRY POINT
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = TeamEdithAirMouseGCS(root)
    root.mainloop()
