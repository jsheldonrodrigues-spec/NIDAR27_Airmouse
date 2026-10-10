"""
================================================================================
TEAM EDITH - AIR MOUSE GROUND CONTROL STATION (GCS)
Autonomous GPS-Denied Indoor Search, Mapping & Survivor Localization Challenge
PS2: NIDAR AirMouse Challenge | Track 1
================================================================================
"""

import tkinter as tk
from tkinter import ttk
import math
import time
import random
import threading
import os
import sys

# Platform audio support
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


# ==============================================================================
# COLOR PALETTE & AESTHETICS (Dark Navy Aerospace Theme - Exact Locked Layout)
# ==============================================================================
COLOR_BG_ROOT          = "#070B16"  # Deepest tactical space navy
COLOR_PANEL_BG         = "#0D1424"  # Dark navy container cards
COLOR_PANEL_BORDER     = "#1C2740"  # Structural card borders
COLOR_HEADER_BG        = "#0A1020"  # Top app bar background
COLOR_CARD_HEADER_BG   = "#131E35"  # Highlighted tab header bar background
COLOR_CANVAS_BLACK     = "#000000"  # Pitch black for SLAM & Video

# Accent Palette
COLOR_CYAN             = "#00F2FE"  # Primary laser & trajectory accent
COLOR_ORANGE           = "#FF6B00"  # Hazard orange (targets, warnings)
COLOR_GREEN            = "#10B981"  # Operational status green
COLOR_RED              = "#EF4444"  # Emergency abort red
COLOR_AMBER            = "#F59E0B"  # Searching / caution amber
COLOR_TEXT_PRIMARY     = "#FFFFFF"  # Crisp signal white
COLOR_TEXT_SECONDARY   = "#94A3B8"  # Secondary slate grey
COLOR_TEXT_MUTED       = "#475569"  # Grid and coordinate labels


# ==============================================================================
# SOUND ALERT SYSTEM (Sonar Chirp & Victory Alarm)
# ==============================================================================
class AudioAlertSystem:
    @staticmethod
    def play_sonar_chirp():
        """Plays high-frequency tactical sonar pulse (880Hz -> 1200Hz) when survivor located."""
        def _beep():
            try:
                if HAS_WINSOUND:
                    winsound.Beep(880, 80)
                    winsound.Beep(1200, 120)
                else:
                    sys.stdout.write('\a')
                    sys.stdout.flush()
            except Exception:
                pass
        threading.Thread(target=_beep, daemon=True).start()

    @staticmethod
    def play_victory_alarm():
        """Distinct 3-tone victory chime on 6th target acquisition."""
        def _chime():
            try:
                if HAS_WINSOUND:
                    winsound.Beep(988, 120)
                    time.sleep(0.05)
                    winsound.Beep(1175, 120)
                    time.sleep(0.05)
                    winsound.Beep(1568, 350)
                else:
                    for _ in range(3):
                        sys.stdout.write('\a')
                        sys.stdout.flush()
                        time.sleep(0.1)
            except Exception:
                pass
        threading.Thread(target=_chime, daemon=True).start()


# ==============================================================================
# MAIN GCS APPLICATION CLASS
# ==============================================================================
class TeamEdithAirMouseGCS:
    def __init__(self, root):
        self.root = root
        self.root.title("TEAM EDITH | AIR MOUSE GCS - Autonomous Aerospace")
        self.root.geometry("1366x768")
        self.root.minsize(1200, 720)
        self.root.configure(bg=COLOR_BG_ROOT)

        # Base Directory for Assets
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Mission State
        self.is_mission_active = False
        self.is_simulation_mode = True
        self.start_time = None
        self.elapsed_time = 0.0

        # Drone State
        self.altitude = 1.20
        self.pitch = 1.8
        self.roll = -0.4
        self.yaw = 198.0
        self.battery_pct = 88
        self.battery_voltage = 22.8
        self.distance_traversed = 42.8
        self.exploration_percent = 74.0

        # ----------------------------------------------------------------------
        # CORRIDOR WAYPOINTS (100% COLLISION-FREE HALLWAY CENTERLINE)
        # Follows the exact indoor hallway corridor between inner and outer walls
        # ----------------------------------------------------------------------
        self.corridor_waypoints = [
            (255, 52),   # Top Entrance near E-13
            (255, 90),   # Moving into North Junction
            (290, 104),  # Northern Hallway Start
            (380, 105),  # Northern Hallway Mid
            (500, 107),  # Northern Hallway East End
            (555, 128),  # North-East Corner Turn
            (566, 175),  # Eastern Hallway Center
            (568, 220),  # Eastern Hallway Southward
            (550, 255),  # South-East Corner Turn
            (500, 258),  # Southern Hallway East
            (410, 248),  # Southern Hallway Center
            (310, 238),  # Southern Hallway West
            (235, 240),  # South-West Corner Turn
            (210, 220),  # Western Hallway Upwards
            (205, 160),  # Past Entry/Exit LZ & T1 Survivor [C-4]
            (215, 125),  # Western Hallway North End
            (235, 105),  # Rejoining Northern Loop
        ]
        self.waypoint_index = 0
        self.waypoint_t = 0.0  # Interpolation factor [0.0, 1.0]
        self.drone_pos = list(self.corridor_waypoints[0])
        self.trajectory_history = []
        self.lidar_angle = 0.0

        # Blinking REC dot state
        self.rec_blink_state = True
        self.last_blink_time = time.time()

        # Survivors Tracker (T1 to T6)
        self.survivors = [
            {"id": "T1", "status": "LOCATED", "grid": "Grid [C-4]", "conf": 94.2, "located": True},
            {"id": "T2", "status": "SEARCHING...", "grid": "--", "conf": 0.0, "located": False},
            {"id": "T3", "status": "SEARCHING...", "grid": "--", "conf": 0.0, "located": False},
            {"id": "T4", "status": "SEARCHING...", "grid": "--", "conf": 0.0, "located": False},
            {"id": "T5", "status": "SEARCHING...", "grid": "--", "conf": 0.0, "located": False},
            {"id": "T6", "status": "SEARCHING...", "grid": "--", "conf": 0.0, "located": False},
        ]
        self.survivors_located_count = 1

        # Setup GUI Components
        self._build_top_header()
        self._build_main_layout()

        # Load Image Assets
        self._load_image_assets()

        # Start periodic updates (60 FPS tick)
        self._schedule_updates()

    # --------------------------------------------------------------------------
    # IMAGE ASSETS LOADER
    # --------------------------------------------------------------------------
    def _load_image_assets(self):
        """Loads high-res authentic LiDAR SLAM map & IP camera surveillance feed."""
        # 1. Camera Feed
        cam_path = os.path.join(self.base_dir, "cam_feed.png")
        if os.path.exists(cam_path):
            try:
                self.cam_photo = tk.PhotoImage(file=cam_path)
            except Exception as e:
                print(f"Error loading cam_feed.png: {e}")
                self.cam_photo = None
        else:
            self.cam_photo = None

        # 2. SLAM Map Background
        slam_path = os.path.join(self.base_dir, "slam_background.png")
        if os.path.exists(slam_path):
            try:
                self.slam_photo = tk.PhotoImage(file=slam_path)
            except Exception as e:
                print(f"Error loading slam_background.png: {e}")
                self.slam_photo = None
        else:
            self.slam_photo = None

    # --------------------------------------------------------------------------
    # 1. TOP HEADER APP BAR
    # --------------------------------------------------------------------------
    def _build_top_header(self):
        self.header_frame = tk.Frame(self.root, bg=COLOR_HEADER_BG, height=62, bd=0)
        self.header_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(6, 4))
        self.header_frame.pack_propagate(False)

        # Left: Team Brand Text
        brand_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        brand_frame.pack(side=tk.LEFT, padx=12, pady=4)

        lbl_title = tk.Label(brand_frame, text="TEAM EDITH", font=("Segoe UI", 15, "bold"),
                             fg=COLOR_TEXT_PRIMARY, bg=COLOR_HEADER_BG)
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(brand_frame, text="TACTICAL DRONE GROUND CONTROL STATION",
                           font=("Segoe UI", 7, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_HEADER_BG)
        lbl_sub.pack(anchor="w")

        # Center: Telemetry Status & Mode Switch
        center_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        center_frame.pack(side=tk.LEFT, expand=True)

        self.lbl_telemetry_status = tk.Label(
            center_frame,
            text="STATUS: ARMED  |  ALT: 1.2m  |  MISSION TIME: 00:00:26.4",
            font=("Consolas", 11, "bold"),
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_HEADER_BG
        )
        self.lbl_telemetry_status.pack(pady=(2, 2))

        # Mode Indicator Pill
        self.lbl_mode_pill = tk.Label(
            center_frame,
            text="[SIMULATION (ACTIVE)]  /  [LIVE HARDWARE]",
            font=("Consolas", 8, "bold"),
            fg=COLOR_GREEN,
            bg="#0E231F",
            padx=10,
            pady=1,
            relief=tk.SOLID,
            bd=1
        )
        self.lbl_mode_pill.pack()

        # Right: RF Telemetry & Battery Monitor
        right_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        right_frame.pack(side=tk.RIGHT, padx=14, pady=4)

        # Wi-Fi Link
        wifi_box = tk.Frame(right_frame, bg=COLOR_HEADER_BG)
        wifi_box.pack(side=tk.LEFT, padx=(0, 16))
        lbl_wifi_icon = tk.Label(wifi_box, text="((•))", font=("Consolas", 9, "bold"), fg=COLOR_CYAN, bg=COLOR_HEADER_BG)
        lbl_wifi_icon.pack(anchor="center")
        lbl_wifi_val = tk.Label(wifi_box, text="99% | -42 dBm | Wi-Fi 6", font=("Consolas", 8, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_HEADER_BG)
        lbl_wifi_val.pack()

        # Battery 6S
        bat_box = tk.Frame(right_frame, bg=COLOR_HEADER_BG)
        bat_box.pack(side=tk.LEFT)
        lbl_bat_title = tk.Label(bat_box, text="⚡ 22.8V 6S   88%", font=("Consolas", 9, "bold"), fg=COLOR_GREEN, bg=COLOR_HEADER_BG)
        lbl_bat_title.pack(anchor="e")

        cells_frame = tk.Frame(bat_box, bg=COLOR_HEADER_BG)
        cells_frame.pack(anchor="e")
        for i in range(1, 7):
            c_lbl = tk.Label(cells_frame, text=f"C{i}", font=("Consolas", 6), fg=COLOR_GREEN, bg="#0E2D22", width=3, bd=1, relief=tk.SOLID)
            c_lbl.pack(side=tk.LEFT, padx=1)

    # --------------------------------------------------------------------------
    # 2. MAIN 3-COLUMN & BOTTOM LAYOUT
    # --------------------------------------------------------------------------
    def _build_main_layout(self):
        container = tk.Frame(self.root, bg=COLOR_BG_ROOT)
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))

        # Upper Section (Columns)
        upper_frame = tk.Frame(container, bg=COLOR_BG_ROOT)
        upper_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left Column: Heading Gauge & Diagnostics (Width: 260)
        self.left_col = tk.Frame(upper_frame, bg=COLOR_BG_ROOT, width=260)
        self.left_col.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        self.left_col.pack_propagate(False)

        # Center Column: 2D Robotic SLAM Canvas (Width: Flexible)
        self.center_col = tk.Frame(upper_frame, bg=COLOR_BG_ROOT)
        self.center_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        # Right Column: IP Camera & Survivor Localization Table (Width: 320)
        self.right_col = tk.Frame(upper_frame, bg=COLOR_BG_ROOT, width=320)
        self.right_col.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_col.pack_propagate(False)

        # Lower Section (Event Log + Exploration Metrics + Action Buttons)
        self.bottom_frame = tk.Frame(container, bg=COLOR_BG_ROOT, height=135)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0))
        self.bottom_frame.pack_propagate(False)

        # Populate Modules
        self._build_left_modules()
        self._build_center_slam_module()
        self._build_right_modules()
        self._build_bottom_modules()

    # --------------------------------------------------------------------------
    # 3. LEFT COLUMN: COMPASS & HARDWARE HEALTH
    # --------------------------------------------------------------------------
    def _build_left_modules(self):
        # 3A. 360° Heading Gauge Card
        self.card_compass = self._create_card(self.left_col, "360° HEADING GAUGE")
        self.card_compass.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        self.compass_canvas = tk.Canvas(self.card_compass, bg=COLOR_PANEL_BG, height=175,
                                        highlightthickness=0, bd=0)
        self.compass_canvas.pack(fill=tk.X, padx=4, pady=2)

        # Pitch / Roll / Yaw Numbers
        tele_box = tk.Frame(self.card_compass, bg=COLOR_PANEL_BG)
        tele_box.pack(fill=tk.X, padx=8, pady=(0, 8))

        p_frame = tk.Frame(tele_box, bg=COLOR_PANEL_BG)
        p_frame.pack(side=tk.LEFT, expand=True)
        tk.Label(p_frame, text="Pitch", font=("Consolas", 7), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG).pack()
        self.lbl_pitch = tk.Label(p_frame, text="+1.8°", font=("Consolas", 10, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG)
        self.lbl_pitch.pack()

        r_frame = tk.Frame(tele_box, bg=COLOR_PANEL_BG)
        r_frame.pack(side=tk.LEFT, expand=True)
        tk.Label(r_frame, text="Roll", font=("Consolas", 7), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG).pack()
        self.lbl_roll = tk.Label(r_frame, text="-0.4°", font=("Consolas", 10, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG)
        self.lbl_roll.pack()

        y_frame = tk.Frame(tele_box, bg=COLOR_PANEL_BG)
        y_frame.pack(side=tk.LEFT, expand=True)
        tk.Label(y_frame, text="Yaw", font=("Consolas", 7), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG).pack()
        self.lbl_yaw = tk.Label(y_frame, text="198°", font=("Consolas", 10, "bold"), fg=COLOR_CYAN, bg=COLOR_PANEL_BG)
        self.lbl_yaw.pack()

        # 3B. 4-System Hardware Health Matrix Card
        self.card_health = self._create_card(self.left_col, "4-SYSTEM HARDWARE HEALTH MATRIX")
        self.card_health.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tbl = tk.Frame(self.card_health, bg=COLOR_PANEL_BG)
        tbl.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # Table Header
        h_row = tk.Frame(tbl, bg=COLOR_PANEL_BG)
        h_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(h_row, text="SYSTEM", font=("Consolas", 7, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG).pack(side=tk.LEFT)
        tk.Label(h_row, text="TEMPERATURE", font=("Consolas", 7, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG).pack(side=tk.RIGHT)

        hw_items = [
            ("MicoAir FC", "38°C", COLOR_GREEN),
            ("Jetson Orin Nano", "51°C", COLOR_AMBER),
            ("ESC Motors", "44°C", COLOR_GREEN),
            ("Raspberry Pi 4", "46°C", COLOR_GREEN)
        ]

        for name, val, col in hw_items:
            row = tk.Frame(tbl, bg=COLOR_PANEL_BG)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=name, font=("Segoe UI", 9), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG).pack(side=tk.LEFT)
            tk.Label(row, text=val, font=("Consolas", 9, "bold"), fg=col, bg=COLOR_PANEL_BG).pack(side=tk.RIGHT)

    # --------------------------------------------------------------------------
    # 4. CENTER: 2D ROBOTIC SLAM CANVAS MODULE
    # --------------------------------------------------------------------------
    def _build_center_slam_module(self):
        self.card_slam = self._create_card(self.center_col, "2D ROBOTIC SLAM CANVAS")
        self.card_slam.pack(fill=tk.BOTH, expand=True)

        self.slam_canvas = tk.Canvas(
            self.card_slam,
            bg=COLOR_CANVAS_BLACK,
            highlightthickness=0,
            bd=0
        )
        self.slam_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    # --------------------------------------------------------------------------
    # 5. RIGHT COLUMN: IP CAMERA & SURVIVOR LOCALIZATION TABLE
    # --------------------------------------------------------------------------
    def _build_right_modules(self):
        # 5A. IP Camera Card
        self.card_cam = self._create_card(self.right_col, "IP CAMERA (30 FPS)")
        self.card_cam.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        self.cam_canvas = tk.Canvas(
            self.card_cam,
            bg=COLOR_CANVAS_BLACK,
            height=162,
            highlightthickness=0,
            bd=0
        )
        self.cam_canvas.pack(fill=tk.X, padx=4, pady=4)

        # 5B. Survivor Localization Table Card
        self.card_survivors = self._create_card(self.right_col, "SURVIVOR LOCALIZATION TABLE (1/6 LOCATED)")
        self.card_survivors.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tbl = tk.Frame(self.card_survivors, bg=COLOR_PANEL_BG)
        tbl.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        # Table Column Header
        h_row = tk.Frame(tbl, bg=COLOR_PANEL_BG)
        h_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(h_row, text="[ID]", font=("Consolas", 7, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, width=4, anchor="w").pack(side=tk.LEFT)
        tk.Label(h_row, text="STATUS", font=("Consolas", 7, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, width=9, anchor="w").pack(side=tk.LEFT)
        tk.Label(h_row, text="GRID COORD", font=("Consolas", 7, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, width=11, anchor="center").pack(side=tk.LEFT)
        tk.Label(h_row, text="CONF%", font=("Consolas", 7, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, width=6, anchor="e").pack(side=tk.RIGHT)

        self.survivor_row_widgets = []
        for s in self.survivors:
            row_bg = "#261304" if s["located"] else COLOR_PANEL_BG
            row = tk.Frame(tbl, bg=row_bg, bd=1, relief=tk.SOLID if s["located"] else tk.FLAT)
            row.pack(fill=tk.X, pady=2, ipady=1)

            # Icon / ID
            lbl_id = tk.Label(row, text=f"🛡 {s['id']}", font=("Consolas", 8, "bold"),
                              fg=COLOR_ORANGE if s["located"] else COLOR_TEXT_SECONDARY, bg=row_bg, width=5, anchor="w")
            lbl_id.pack(side=tk.LEFT)

            # Status
            lbl_status = tk.Label(row, text=s["status"], font=("Consolas", 7, "bold"),
                                  fg=COLOR_ORANGE if s["located"] else COLOR_TEXT_MUTED, bg=row_bg, width=10, anchor="w")
            lbl_status.pack(side=tk.LEFT)

            # Grid Coordinate
            lbl_grid = tk.Label(row, text=s["grid"], font=("Consolas", 8, "bold"),
                                fg=COLOR_ORANGE if s["located"] else COLOR_TEXT_MUTED, bg=row_bg, width=11, anchor="center")
            lbl_grid.pack(side=tk.LEFT)

            # Confidence
            conf_str = f"{s['conf']:.1f}%" if s["located"] else "-"
            lbl_conf = tk.Label(row, text=conf_str, font=("Consolas", 8, "bold"),
                                fg=COLOR_GREEN if s["located"] else COLOR_TEXT_MUTED, bg=row_bg, width=6, anchor="e")
            lbl_conf.pack(side=tk.RIGHT)

            self.survivor_row_widgets.append((lbl_status, lbl_grid, lbl_conf, row))

    # --------------------------------------------------------------------------
    # 6. BOTTOM ROW: LOG + PROGRESS + ACTION BUTTONS
    # --------------------------------------------------------------------------
    def _build_bottom_modules(self):
        # 6A. Mission Event Log (Left)
        card_log = self._create_card(self.bottom_frame, "MISSION EVENT LOG")
        card_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        self.log_text = tk.Text(card_log, bg="#070B16", fg=COLOR_TEXT_SECONDARY,
                                font=("Consolas", 8), bd=0, highlightthickness=0, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        initial_logs = [
            "[15:56:01] System Initialized: MicoAir FC + Jetson Orin Nano Online",
            "[15:56:02] LiDAR RPLiDAR A2 Active: 12.0 Hz Spin Rate (1440 pts/rev)",
            "[15:56:03] SLAM Odometry: Frontier Exploration Active in Corridor Alpha",
            "[15:56:08] [ALERT] Survivor T1 Identified at Grid [C-4] (Temp: 37.1°C)",
            "[15:56:09] Discrete Geotag Registered: T1 -> Room Alpha [C-4] Locked"
        ]
        for l in initial_logs:
            self.log_text.insert(tk.END, l + "\n")
        self.log_text.see(tk.END)

        # 6B. Exploration Progress Card (Center)
        card_prog = self._create_card(self.bottom_frame, "MISSION PROGRESS & ARENA EXPLORATION")
        card_prog.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6), ipadx=10)

        prog_inner = tk.Frame(card_prog, bg=COLOR_PANEL_BG)
        prog_inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        self.lbl_arena_pct = tk.Label(prog_inner, text="ARENA EXPLORED: 74%", font=("Consolas", 10, "bold"),
                                      fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, anchor="w")
        self.lbl_arena_pct.pack(fill=tk.X, pady=(2, 4))

        self.prog_canvas = tk.Canvas(prog_inner, bg="#0A1020", height=12, highlightthickness=0, bd=0)
        self.prog_canvas.pack(fill=tk.X, pady=(0, 6))

        self.lbl_stats = tk.Label(
            prog_inner,
            text="PHASE: CORRIDOR MAPPING\nDISTANCE: 42.8m  |  TARGETS: 1 / 6 FOUND",
            font=("Consolas", 8),
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_PANEL_BG,
            justify=tk.LEFT,
            anchor="w"
        )
        self.lbl_stats.pack(fill=tk.X)

        # 6C. Control Buttons (Right)
        btn_frame = tk.Frame(self.bottom_frame, bg=COLOR_BG_ROOT, width=200)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)
        btn_frame.pack_propagate(False)

        self.btn_start = tk.Button(
            btn_frame,
            text="START MISSION",
            font=("Segoe UI", 10, "bold"),
            bg="#059669",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#10B981",
            activeforeground=COLOR_TEXT_PRIMARY,
            bd=0,
            cursor="hand2",
            command=self._start_mission
        )
        self.btn_start.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        self.btn_abort = tk.Button(
            btn_frame,
            text="EMERGENCY ABORT (RTL)",
            font=("Segoe UI", 9, "bold"),
            bg="#DC2626",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#EF4444",
            activeforeground=COLOR_TEXT_PRIMARY,
            bd=0,
            cursor="hand2",
            command=self._emergency_abort
        )
        self.btn_abort.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    # --------------------------------------------------------------------------
    # HELPER: CARD CREATOR
    # --------------------------------------------------------------------------
    def _create_card(self, parent, title_text):
        card = tk.Frame(parent, bg=COLOR_PANEL_BG, bd=1, relief=tk.SOLID,
                        highlightbackground=COLOR_PANEL_BORDER, highlightthickness=1)

        # Header Bar
        hdr = tk.Frame(card, bg=COLOR_CARD_HEADER_BG, height=24)
        hdr.pack(fill=tk.X, side=tk.TOP)
        hdr.pack_propagate(False)

        # Neon Accent Bar
        accent = tk.Frame(hdr, bg=COLOR_CYAN, width=3)
        accent.pack(side=tk.LEFT, fill=tk.Y)

        lbl = tk.Label(hdr, text=f" {title_text}", font=("Consolas", 8, "bold"),
                       fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_HEADER_BG)
        lbl.pack(side=tk.LEFT, padx=4)

        return card

    # --------------------------------------------------------------------------
    # RENDERING ENGINES
    # --------------------------------------------------------------------------
    def _render_compass(self):
        self.compass_canvas.delete("all")
        w = self.compass_canvas.winfo_width()
        h = self.compass_canvas.winfo_height()
        if w < 20 or h < 20:
            return

        cx = w / 2.0
        cy = h / 2.0
        r = min(cx, cy) - 10

        # Outer Dials
        self.compass_canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#1E2A42", width=3)
        self.compass_canvas.create_oval(cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8, outline="#00354A", width=1)

        # Tick marks
        for deg in range(0, 360, 30):
            rad = math.radians(deg)
            x1 = cx + (r - 4) * math.sin(rad)
            y1 = cy - (r - 4) * math.cos(rad)
            x2 = cx + (r - 12) * math.sin(rad)
            y2 = cy - (r - 12) * math.cos(rad)
            col = COLOR_RED if deg == 0 else "#334155"
            self.compass_canvas.create_line(x1, y1, x2, y2, fill=col, width=2 if deg % 90 == 0 else 1)

        # North marker
        self.compass_canvas.create_text(cx, cy - r + 20, text="N", font=("Consolas", 9, "bold"), fill=COLOR_RED)
        self.compass_canvas.create_text(cx + r - 20, cy, text="E", font=("Consolas", 8, "bold"), fill=COLOR_TEXT_SECONDARY)
        self.compass_canvas.create_text(cx, cy + r - 20, text="S", font=("Consolas", 8, "bold"), fill=COLOR_TEXT_SECONDARY)
        self.compass_canvas.create_text(cx - r + 20, cy, text="W", font=("Consolas", 8, "bold"), fill=COLOR_TEXT_SECONDARY)

        # Orange Needle pointing to current Yaw
        yaw_rad = math.radians(self.yaw)
        nx = cx + (r - 24) * math.sin(yaw_rad)
        ny = cy - (r - 24) * math.cos(yaw_rad)
        bx = cx - (r - 24) * 0.4 * math.sin(yaw_rad)
        by = cy + (r - 24) * 0.4 * math.cos(yaw_rad)
        self.compass_canvas.create_line(bx, by, nx, ny, fill=COLOR_ORANGE, width=3, arrow=tk.LAST, arrowshape=(10, 12, 4))

        # Center Dial Digital Readout
        self.compass_canvas.create_oval(cx - 22, cy - 22, cx + 22, cy + 22, fill="#070B16", outline=COLOR_CYAN, width=1.5)
        self.compass_canvas.create_text(cx, cy - 4, text=f"{int(self.yaw)}°", font=("Consolas", 10, "bold"), fill=COLOR_TEXT_PRIMARY)

        # Direction text
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        d_idx = int((self.yaw + 22.5) % 360 // 45)
        self.compass_canvas.create_text(cx, cy + 9, text=dirs[d_idx], font=("Consolas", 7, "bold"), fill=COLOR_CYAN)

    def _render_ip_camera(self):
        self.cam_canvas.delete("all")
        w = self.cam_canvas.winfo_width()
        h = self.cam_canvas.winfo_height()
        if w < 20 or h < 20:
            return

        # 1. Background Frame (Display cropped realistic surveillance image if loaded)
        if self.cam_photo:
            self.cam_canvas.create_image(0, 0, anchor="nw", image=self.cam_photo)
        else:
            # Fallback high-contrast corridor mockup
            self.cam_canvas.create_rectangle(0, 0, w, h, fill="#121824", outline="")
            self.cam_canvas.create_line(0, 0, w * 0.35, h * 0.45, fill="#1F293D")
            self.cam_canvas.create_line(w, 0, w * 0.65, h * 0.45, fill="#1F293D")
            self.cam_canvas.create_line(0, h, w * 0.35, h * 0.65, fill="#1F293D")
            self.cam_canvas.create_line(w, h, w * 0.65, h * 0.65, fill="#1F293D")

            # Center target silhouette
            cx, cy = w / 2.0, h / 2.0
            self.cam_canvas.create_oval(cx - 10, cy - 25, cx + 10, cy - 5, fill="#334155", outline="")
            self.cam_canvas.create_rectangle(cx - 16, cy - 5, cx + 16, cy + 30, fill="#334155", outline="")

        # 2. Dynamic Blinking REC Indicator
        now = time.time()
        if now - self.last_blink_time > 0.5:
            self.rec_blink_state = not self.rec_blink_state
            self.last_blink_time = now

        if self.rec_blink_state:
            self.cam_canvas.create_oval(10, 10, 20, 20, fill=COLOR_RED, outline="")
        self.cam_canvas.create_text(35, 15, text="REC", font=("Consolas", 8, "bold"), fill=COLOR_TEXT_PRIMARY)

        # 3. Dynamic Live OSD Timestamp
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        self.cam_canvas.create_text(w - 75, 15, text=ts, font=("Consolas", 7), fill=COLOR_TEXT_PRIMARY)

        # 4. YOLO Target Reticle & Bounding Box Overlay
        if self.survivors[0]["located"]:
            # Highlight box over the person in corridor
            bx1, by1, bx2, by2 = 145, 32, 210, 132
            self.cam_canvas.create_rectangle(bx1, by1, bx2, by2, outline=COLOR_ORANGE, width=2)
            self.cam_canvas.create_rectangle(bx1, by1 - 15, bx1 + 135, by1, fill=COLOR_ORANGE, outline="")
            self.cam_canvas.create_text(bx1 + 67, by1 - 7, text="[SURVIVOR T1: 94.2% CONF]",
                                        font=("Consolas", 7, "bold"), fill=COLOR_TEXT_PRIMARY)

        # Bottom OSD status
        self.cam_canvas.create_text(60, h - 12, text="[SOLOv8 T1: target]", font=("Consolas", 7), fill=COLOR_TEXT_SECONDARY)
        self.cam_canvas.create_text(w - 45, h - 12, text="30.0 FPS", font=("Consolas", 7, "bold"), fill=COLOR_CYAN)

    def _render_slam_canvas(self):
        self.slam_canvas.delete("all")
        cw = self.slam_canvas.winfo_width()
        ch = self.slam_canvas.winfo_height()
        if cw < 50 or ch < 50:
            return

        # 1. Authentic High-Res Point Cloud Map (Floorplan with corridors and walls)
        if self.slam_photo:
            self.slam_canvas.create_image(0, 0, anchor="nw", image=self.slam_photo)
        else:
            # Fallback grid background
            self.slam_canvas.create_rectangle(0, 0, cw, ch, fill=COLOR_CANVAS_BLACK)
            for i in range(16):
                x = (cw / 15.0) * i
                self.slam_canvas.create_line(x, 0, x, ch, fill="#0F182A")
                y = (ch / 15.0) * i
                self.slam_canvas.create_line(0, y, cw, y, fill="#0F182A")

        # 2. Dynamic Trajectory Trail (Smooth Glowing Cyan Ribbon)
        if len(self.trajectory_history) > 1:
            flat_coords = []
            for hx, hy in self.trajectory_history:
                flat_coords.extend([hx, hy])
            # Draw glow underlay
            self.slam_canvas.create_line(flat_coords, fill="#00607A", width=5, smooth=True)
            # Draw sharp core cyan line
            self.slam_canvas.create_line(flat_coords, fill=COLOR_CYAN, width=2.5, smooth=True)

        # 3. Rotating 360° LiDAR Laser Sweep Cone
        dx, dy = self.drone_pos
        cone_radius = 55
        sweep_rad = math.radians(self.lidar_angle)
        span = math.radians(35)
        x1 = dx + cone_radius * math.cos(sweep_rad - span)
        y1 = dy + cone_radius * math.sin(sweep_rad - span)
        x2 = dx + cone_radius * math.cos(sweep_rad + span)
        y2 = dy + cone_radius * math.sin(sweep_rad + span)
        self.slam_canvas.create_polygon(dx, dy, x1, y1, x2, y2, fill="#00354A", outline="")

        # 4. Entry/Exit LZ Marker
        lz_x, lz_y = 205, 160
        self.slam_canvas.create_oval(lz_x - 7, lz_y - 7, lz_x + 7, lz_y + 7, fill=COLOR_GREEN, outline=COLOR_TEXT_PRIMARY, width=1.5)
        self.slam_canvas.create_text(lz_x - 38, lz_y, text="Entry/Exit LZ", font=("Consolas", 7, "bold"), fill=COLOR_GREEN)

        # 5. Survivor T1 Marker (Glowing Orange Pin)
        if self.survivors[0]["located"]:
            t1_x, t1_y = 205, 160
            self.slam_canvas.create_oval(t1_x - 8, t1_y - 8, t1_x + 8, t1_y + 8, fill=COLOR_ORANGE, outline=COLOR_TEXT_PRIMARY, width=2)
            self.slam_canvas.create_text(t1_x + 22, t1_y - 10, text="T1 [C-4]", font=("Consolas", 8, "bold"), fill=COLOR_ORANGE)

        # 6. Drone Symbol (Tactical Quadcopter with Heading Vector)
        # Heading Vector
        h_rad = math.radians(self.yaw)
        hx = dx + 18 * math.sin(h_rad)
        hy = dy - 18 * math.cos(h_rad)
        self.slam_canvas.create_line(dx, dy, hx, hy, fill=COLOR_CYAN, width=2, arrow=tk.LAST, arrowshape=(6, 8, 3))

        # Quadcopter Halo & Core
        self.slam_canvas.create_oval(dx - 10, dy - 10, dx + 10, dy + 10, outline=COLOR_ORANGE, width=1.5)
        self.slam_canvas.create_oval(dx - 4, dy - 4, dx + 4, dy + 4, fill=COLOR_ORANGE, outline="")
        self.slam_canvas.create_line(dx - 8, dy, dx + 8, dy, fill=COLOR_TEXT_PRIMARY, width=1.5)
        self.slam_canvas.create_line(dx, dy - 8, dx, dy + 8, fill=COLOR_TEXT_PRIMARY, width=1.5)

    def _render_progress_bar(self):
        self.prog_canvas.delete("all")
        pw = self.prog_canvas.winfo_width()
        ph = self.prog_canvas.winfo_height()
        if pw < 10 or ph < 4:
            return

        self.prog_canvas.create_rectangle(0, 0, pw, ph, fill="#0A1020", outline="#1E2A42")
        fill_w = (self.exploration_percent / 100.0) * pw
        self.prog_canvas.create_rectangle(0, 0, fill_w, ph, fill=COLOR_CYAN, outline="")

        self.lbl_arena_pct.config(text=f"ARENA EXPLORED: {int(self.exploration_percent)}%")
        self.lbl_stats.config(
            text=f"PHASE: CORRIDOR MAPPING\nDISTANCE: {self.distance_traversed:.1f}m  |  TARGETS: {self.survivors_located_count} / 6 FOUND"
        )

    # --------------------------------------------------------------------------
    # PERIODIC SIMULATION ENGINE (60 FPS TICK)
    # --------------------------------------------------------------------------
    def _schedule_updates(self):
        self._update_simulation_tick()
        self.root.after(33, self._schedule_updates)  # ~30 FPS UI refresh

    def _update_simulation_tick(self):
        # 1. Update Mission Time
        if self.is_mission_active and self.start_time:
            self.elapsed_time = time.time() - self.start_time
            m = int(self.elapsed_time // 60)
            s = int(self.elapsed_time % 60)
            ms = int((self.elapsed_time * 10) % 10)
            self.lbl_telemetry_status.config(
                text=f"STATUS: ARMED  |  ALT: {self.altitude:.1f}m  |  MISSION TIME: 00:{m:02d}:{s:02d}.{ms:01d}"
            )

        # 2. Spin LiDAR
        self.lidar_angle = (self.lidar_angle + 8.0) % 360.0

        # 3. Advance Drone Along Corridor Waypoints
        if self.is_mission_active:
            self._advance_corridor_flight()

        # 4. Render UI Elements
        self._render_compass()
        self._render_ip_camera()
        self._render_slam_canvas()
        self._render_progress_bar()

    def _advance_corridor_flight(self):
        """Moves drone smoothly along predefined hallway centerline (100% collision-free)."""
        p1 = self.corridor_waypoints[self.waypoint_index]
        next_idx = (self.waypoint_index + 1) % len(self.corridor_waypoints)
        p2 = self.corridor_waypoints[next_idx]

        # Interpolate between p1 and p2
        step_speed = 0.035
        self.waypoint_t += step_speed

        if self.waypoint_t >= 1.0:
            self.waypoint_t = 0.0
            self.waypoint_index = next_idx
            p1 = p2
            next_idx = (self.waypoint_index + 1) % len(self.corridor_waypoints)
            p2 = self.corridor_waypoints[next_idx]

        # Calculate current (x, y)
        cur_x = p1[0] + (p2[0] - p1[0]) * self.waypoint_t
        cur_y = p1[1] + (p2[1] - p1[1]) * self.waypoint_t
        self.drone_pos = [cur_x, cur_y]

        # Calculate heading angle (Yaw) dynamically from movement vector
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        heading_deg = (math.degrees(math.atan2(dx, -dy))) % 360.0
        self.yaw = heading_deg
        self.lbl_yaw.config(text=f"{int(self.yaw)}°")

        # Record Trajectory History
        self.trajectory_history.append(list(self.drone_pos))
        if len(self.trajectory_history) > 400:
            self.trajectory_history.pop(0)

        # Update Exploration Metrics
        self.distance_traversed += 0.05
        self.exploration_percent = min(96.0, self.exploration_percent + 0.02)

        # Trigger Survivor T1 Acquisition if passing near T1 and not yet alerted
        if self.waypoint_index == 14 and self.elapsed_time >= 3.0:
            if not self.survivors[0]["located"]:
                self.survivors[0]["located"] = True
                self._log_event("[ALERT] Survivor T1 Acquired at Grid [C-4] (YOLO Conf: 94.2%)")
                AudioAlertSystem.play_sonar_chirp()

    def _log_event(self, message):
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {message}\n")
        self.log_text.see(tk.END)

    # --------------------------------------------------------------------------
    # PILOT ACTIONS
    # --------------------------------------------------------------------------
    def _start_mission(self):
        if not self.is_mission_active:
            self.is_mission_active = True
            self.start_time = time.time()
            self._log_event("[MISSION] Autonomous Takeoff Initialized -> Target Altitude: 1.2m")
            self._log_event("[NAV] Traversed Corridor Exploration Active (Frontier SLAM)")
            self.btn_start.config(text="MISSION ACTIVE", bg=COLOR_AMBER)
            AudioAlertSystem.play_sonar_chirp()

    def _emergency_abort(self):
        self.is_mission_active = False
        self._log_event("[ALERT] EMERGENCY ABORT (RTL) TRIGGERED BY PILOT!")
        self._log_event("[RTL] Safe Return-to-Launch Initiated along Hallway Path -> Returning to LZ")
        self.btn_start.config(text="START MISSION", bg="#059669")
        AudioAlertSystem.play_sonar_chirp()


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    app_root = tk.Tk()
    app = TeamEdithAirMouseGCS(app_root)
    app_root.mainloop()
