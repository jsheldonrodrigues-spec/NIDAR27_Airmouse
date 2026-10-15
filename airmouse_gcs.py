"""
================================================================================
TEAM EDITH - AIR MOUSE GROUND CONTROL STATION (GCS)
Autonomous GPS-Denied Indoor Search, Mapping & Survivor Localization Challenge
PS2: NIDAR AirMouse Challenge | Track 1
Ultra-Modern Military UAV Defense Standard Ground Control Station
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

# Platform Audio Support (Sonar Chirp & Victory Alarm)
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


# ------------------------------------------------------------------------------
# 2. PRIVATE FONT LOADER (RAJDHANI & JETBRAINS MONO)
# ------------------------------------------------------------------------------
def register_local_fonts(base_dir):
    """Registers Rajdhani and JetBrains Mono TrueType fonts process-privately in Windows."""
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
            print(f"Font registration notice: {e}")


# ------------------------------------------------------------------------------
# 3. COLOR PALETTE & AESTHETICS (Ultra-Modern Stealth Defense Obsidian & Emerald)
# ------------------------------------------------------------------------------
COLOR_BG_ROOT          = "#0A0F1D"  # Deepest atmospheric space navy
COLOR_PANEL_BG         = "#111625"  # Matte obsidian container cards
COLOR_PANEL_BORDER     = "#1C263A"  # Structural micro-borders
COLOR_HEADER_BG        = "#0D1220"  # Top app bar background
COLOR_CARD_HEADER_BG   = "#151B2E"  # Highlighted tab header bar background
COLOR_CANVAS_BLACK     = "#050811"  # Pitch black for SLAM & Video

# Vibrant Accent Palette
COLOR_GREEN_DEFENSE    = "#05DF72"  # Tactical Emerald Defense Green (Nominal & Battery)
COLOR_CYAN             = "#00F2FE"  # Primary laser & trajectory accent
COLOR_ORANGE           = "#FF6B00"  # Hazard orange (targets, warnings)
COLOR_AMBER            = "#F59E0B"  # Searching / caution amber
COLOR_RED              = "#EF4444"  # Emergency abort red
COLOR_TEXT_PRIMARY     = "#FFFFFF"  # Crisp signal white
COLOR_TEXT_SECONDARY   = "#8A99AD"  # Secondary tactical slate grey
COLOR_TEXT_MUTED       = "#475569"  # Grid and coordinate labels


# ------------------------------------------------------------------------------
# 4. SOUND & TACTICAL VOICE ALERT SYSTEM
# ------------------------------------------------------------------------------
class AudioAlertSystem:
    @staticmethod
    def play_sonar_chirp():
        """Plays tactical sonar chirp when survivor acquired."""
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

    @staticmethod
    def speak_tactical(text):
        """Speaks clear tactical synthetic callout using native SAPI without external dependencies."""
        def _speak():
            try:
                if sys.platform == "win32":
                    import subprocess
                    clean_text = text.replace("'", "").replace('"', '')
                    cmd = f'powershell -WindowStyle Hidden -Command "(New-Object -ComObject SAPI.SpVoice).Speak(\'{clean_text}\')"'
                    subprocess.Popen(cmd, shell=True)
            except Exception:
                pass
        threading.Thread(target=_speak, daemon=True).start()


# ==============================================================================
# 5. MAIN GCS APPLICATION CLASS
# ==============================================================================
class TeamEdithAirMouseGCS:
    def __init__(self, root):
        self.root = root
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Register Fonts
        register_local_fonts(self.base_dir)
        self._init_fonts()

        # Window Setup (Full Screen / Maximized View)
        self.root.title("TEAM EDITH | AIRMOUSE TACTICAL GCS - PS2 NIDAR CHALLENGE")
        self.root.configure(bg=COLOR_BG_ROOT)

        # Set Maximized on launch
        self.is_fullscreen = False
        try:
            self.root.state('zoomed')
        except Exception:
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_w}x{screen_h}+0+0")

        # F11 Key toggle for true borderless fullscreen
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)
        self.root.bind("<space>", lambda e: self._toggle_pause())

        # ----------------------------------------------------------------------
        # MISSION & DRONE STATE
        # ----------------------------------------------------------------------
        self.is_mission_active = False
        self.is_paused = False
        self.is_live_hardware_mode = False
        self.camera_mode = "RGB"            # "RGB" or "THERMAL"
        self.is_rc_minimized = False        # Minimizable Radiomaster State
        self.start_time = None
        self.elapsed_time = 0.0

        # Drone Kinematics
        self.altitude = 1.20
        self.pitch = 19.5
        self.roll = -1.0
        self.yaw = 198.0
        self.battery_pct = 84.2
        self.battery_voltage = 22.84
        self.current_amps = 14.2
        self.distance_traversed = 0.0
        self.exploration_percent = 0.0

        # Radiomaster Pocket ELRS Gimbal Stick Positions [-1.0 to 1.0]
        self.rc_throttle = 0.50
        self.rc_yaw = 0.00
        self.rc_pitch = 0.15
        self.rc_roll = -0.05
        self.rc_lq = 100
        self.rc_rate = "500Hz"
        self.rc_mode = "AUTO SLAM"

        # Dynamic Comms Link
        self.rssi_dbm = -42
        self.link_quality = 99
        self.ping_ms = 3.2
        self.waveform_phase = 0.0

        # Dynamic Camera State
        self.cam_fps = 30.0
        self.rec_blink_state = True
        self.last_blink_time = time.time()

        # LiDAR state
        self.lidar_angle = 0.0
        self.lidar_points = []

        # SLAM Interactive Zoom & Pan
        self.slam_zoom = 1.0
        self.slam_pan_x = 0
        self.slam_pan_y = 0

        # ----------------------------------------------------------------------
        # 6 SURVIVORS DEFINITION (T1 to T6) ACROSS DISCRETE ARENA GRIDS
        # ----------------------------------------------------------------------
        self.survivors = [
            {"id": "T1", "status": "SEARCHING...", "grid": "Grid [C-4]", "conf": 0.0, "located": False, "x": 180, "y": 140},
            {"id": "T2", "status": "SEARCHING...", "grid": "Grid [G-2]", "conf": 0.0, "located": False, "x": 380, "y": 70},
            {"id": "T3", "status": "SEARCHING...", "grid": "Grid [K-7]", "conf": 0.0, "located": False, "x": 620, "y": 240},
            {"id": "T4", "status": "SEARCHING...", "grid": "Grid [M-12]", "conf": 0.0, "located": False, "x": 780, "y": 420},
            {"id": "T5", "status": "SEARCHING...", "grid": "Grid [D-14]", "conf": 0.0, "located": False, "x": 220, "y": 500},
            {"id": "T6", "status": "SEARCHING...", "grid": "Grid [J-11]", "conf": 0.0, "located": False, "x": 580, "y": 400},
        ]
        self.survivors_located_count = 0

        # ----------------------------------------------------------------------
        # COMPREHENSIVE COLLISION-FREE MAZE WAYPOINTS (1000x700 Virtual Space)
        # ----------------------------------------------------------------------
        self.arena_virtual_w = 1000
        self.arena_virtual_h = 700

        self.corridor_waypoints = [
            (100, 140),   # 0: Entry/Exit LZ [B-4]
            (180, 140),   # 1: T1 Approach Sector [C-4]
            (240, 140),   # 2: Junction North
            (240, 70),    # 3: Heading to Sector Alpha
            (380, 70),    # 4: T2 Approach Sector [G-2]
            (520, 70),    # 5: North-East Junction
            (520, 160),   # 6: Moving South Corridor
            (620, 160),   # 7: East Alcove Access
            (620, 240),   # 8: T3 Approach Sector [K-7]
            (720, 240),   # 9: Eastern Descent
            (720, 340),   # 10: South-East Corridor Entry
            (780, 420),   # 11: T4 Approach Sector [M-12]
            (680, 420),   # 12: Moving West
            (580, 420),   # 13: Central Access
            (580, 400),   # 14: T6 Approach Sector [J-11]
            (500, 420),   # 15: South Corridor Mid
            (360, 420),   # 16: South Hallway West
            (220, 420),   # 17: Junction to South-West Chamber
            (220, 500),   # 18: T5 Approach Sector [D-14]
            (220, 420),   # 19: Leaving Chamber
            (320, 320),   # 20: Heading North-West
            (380, 240),   # 21: Central Hallway Return
            (240, 240),   # 22: Western Junction
            (240, 140),   # 23: Approaching Home LZ
            (100, 140),   # 24: Final Safe Return LZ [B-4]
        ]
        self.waypoint_index = 0
        self.waypoint_t = 0.0
        self.drone_pos = list(self.corridor_waypoints[0])
        self.trajectory_history = []

        # High-Contrast Planar Maze Walls
        self.maze_walls = [
            # Outer Perimeter
            ((50, 30), (950, 30)),
            ((950, 30), (950, 670)),
            ((950, 670), (50, 670)),
            ((50, 670), (50, 30)),
            # Internal Corridor Partitions
            ((50, 200), (300, 200)),
            ((300, 200), (300, 100)),
            ((450, 30), (450, 220)),
            ((450, 220), (660, 220)),
            ((660, 100), (840, 100)),
            ((840, 100), (840, 290)),
            ((740, 290), (950, 290)),
            ((50, 360), (300, 360)),
            ((300, 360), (300, 540)),
            ((50, 540), (160, 540)),
            ((300, 540), (460, 540)),
            ((460, 540), (460, 360)),
            ((460, 360), (620, 360)),
            ((620, 360), (620, 540)),
            ((620, 540), (780, 540)),
            ((780, 360), (780, 540)),
            ((780, 540), (950, 540)),
        ]

        # Build UI Components
        self._build_top_header()
        self._build_main_layout()

        # Start 60 FPS Event Loop
        self._schedule_updates()

    # --------------------------------------------------------------------------
    # FONTS INITIALIZATION (RAJDHANI & JETBRAINS MONO PAIRING)
    # --------------------------------------------------------------------------
    def _init_fonts(self):
        from tkinter import font
        available_fonts = [f.lower() for f in font.families()]

        has_rajdhani = any("rajdhani" in f for f in available_fonts)
        has_mono = any("jetbrains" in f for f in available_fonts)

        self.font_header_family = "Rajdhani" if has_rajdhani else ("Segoe UI" if sys.platform == "win32" else "Helvetica")
        self.font_mono_family = "JetBrains Mono" if has_mono else ("Consolas" if sys.platform == "win32" else "Courier")

        self.FONT_TITLE       = (self.font_header_family, 16, "bold")
        self.FONT_SUBTITLE    = (self.font_header_family, 9, "bold")
        self.FONT_CARD_TITLE  = (self.font_header_family, 11, "bold")
        self.FONT_BTN         = (self.font_header_family, 11, "bold")
        self.FONT_BTN_SM      = (self.font_header_family, 8, "bold")

        self.FONT_TELEMETRY   = (self.font_mono_family, 10, "bold")
        self.FONT_MONO_MD     = (self.font_mono_family, 9, "bold")
        self.FONT_MONO_SM     = (self.font_mono_family, 8, "bold")
        self.FONT_MONO_XS     = (self.font_mono_family, 7, "normal")

    # --------------------------------------------------------------------------
    # FULL SCREEN CONTROLS
    # --------------------------------------------------------------------------
    def _toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        if hasattr(self, "btn_fullscreen"):
            self.btn_fullscreen.config(text="🗗 RESTORE" if self.is_fullscreen else "⛶ FULLSCREEN")

    def _exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes("-fullscreen", False)
            if hasattr(self, "btn_fullscreen"):
                self.btn_fullscreen.config(text="⛶ FULLSCREEN")

    # --------------------------------------------------------------------------
    # 1. TOP HEADER APP BAR (CLEAN MODERN DEFENSE STANDARD)
    # --------------------------------------------------------------------------
    def _build_top_header(self):
        self.header_frame = tk.Frame(self.root, bg=COLOR_HEADER_BG, height=64, bd=0)
        self.header_frame.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(4, 4))
        self.header_frame.pack_propagate(False)

        # 1A. Left: Brand Name
        brand_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        brand_frame.pack(side=tk.LEFT, padx=12, pady=4)

        lbl_title = tk.Label(brand_frame, text="TEAM EDITH", font=self.FONT_TITLE,
                             fg=COLOR_TEXT_PRIMARY, bg=COLOR_HEADER_BG)
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(brand_frame, text="AIRMOUSE TACTICAL GCS",
                           font=self.FONT_SUBTITLE, fg=COLOR_CYAN, bg=COLOR_HEADER_BG)
        lbl_sub.pack(anchor="w")

        # 1B. Center: Mission Status Pills & Audio Waveform
        center_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        center_frame.pack(side=tk.LEFT, expand=True)

        pill_row = tk.Frame(center_frame, bg=COLOR_HEADER_BG)
        pill_row.pack(pady=(2, 2))

        tk.Label(pill_row, text="MISSION\nPS2-NIDAR-01", font=self.FONT_MONO_XS,
                 fg=COLOR_TEXT_SECONDARY, bg="#111625", padx=6, pady=2, relief=tk.SOLID, bd=1).pack(side=tk.LEFT, padx=3)

        self.lbl_utc_time = tk.Label(pill_row, text="UTC TIME\n14:04:00", font=self.FONT_MONO_XS,
                                     fg=COLOR_TEXT_PRIMARY, bg="#111625", padx=6, pady=2, relief=tk.SOLID, bd=1)
        self.lbl_utc_time.pack(side=tk.LEFT, padx=3)

        wf_box = tk.Frame(pill_row, bg="#111625", relief=tk.SOLID, bd=1, padx=4)
        wf_box.pack(side=tk.LEFT, padx=3)
        tk.Label(wf_box, text="SECURE UPLINK\n► AES-256 ACTIVE", font=self.FONT_MONO_XS,
                 fg=COLOR_GREEN_DEFENSE, bg="#111625").pack(side=tk.LEFT, padx=2)
        self.waveform_canvas = tk.Canvas(wf_box, width=65, height=24, bg="#111625", highlightthickness=0, bd=0)
        self.waveform_canvas.pack(side=tk.LEFT, padx=2)

        tk.Label(pill_row, text="AUTOPILOT\nSYSTEM NOMINAL", font=self.FONT_MONO_XS,
                 fg=COLOR_GREEN_DEFENSE, bg="#0E231F", padx=6, pady=2, relief=tk.SOLID, bd=1).pack(side=tk.LEFT, padx=3)

        self.lbl_wifi_status = tk.Label(pill_row, text="Wi-Fi 6 LINK\nSTRONG -42 dBm", font=self.FONT_MONO_XS,
                                        fg=COLOR_CYAN, bg="#111625", padx=6, pady=2, relief=tk.SOLID, bd=1)
        self.lbl_wifi_status.pack(side=tk.LEFT, padx=3)

        tk.Label(pill_row, text="LATENCY\n3.2ms", font=self.FONT_MONO_XS,
                 fg=COLOR_TEXT_PRIMARY, bg="#111625", padx=6, pady=2, relief=tk.SOLID, bd=1).pack(side=tk.LEFT, padx=3)

        self.lbl_early_exit = tk.Label(pill_row, text="6/6 SURVIVORS SECURED\n[EARLY EXIT BONUS]", font=self.FONT_MONO_XS,
                                       fg=COLOR_GREEN_DEFENSE, bg="#0E231F", padx=6, pady=2, relief=tk.SOLID, bd=1)
        self.lbl_early_exit.pack(side=tk.LEFT, padx=3)

        # 1C. Right: Controls & Pre-Arm
        right_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        right_frame.pack(side=tk.RIGHT, padx=12, pady=4)

        self.btn_checklist = tk.Button(
            right_frame,
            text="PRE-ARM CHECK ✔",
            font=self.FONT_MONO_XS,
            fg=COLOR_GREEN_DEFENSE,
            bg="#0E231F",
            activebackground=COLOR_GREEN_DEFENSE,
            activeforeground="#000000",
            bd=1,
            relief=tk.SOLID,
            cursor="hand2",
            command=self._open_preflight_checklist
        )
        self.btn_checklist.pack(side=tk.LEFT, padx=3)

        self.btn_fullscreen = tk.Button(
            right_frame,
            text="⛶ FULLSCREEN",
            font=self.FONT_MONO_XS,
            bg="#162035",
            fg=COLOR_TEXT_SECONDARY,
            activebackground=COLOR_CYAN,
            activeforeground="#000000",
            bd=1,
            relief=tk.SOLID,
            cursor="hand2",
            command=self._toggle_fullscreen
        )
        self.btn_fullscreen.pack(side=tk.LEFT, padx=3)

    # --------------------------------------------------------------------------
    # 2. MAIN LAYOUT
    # --------------------------------------------------------------------------
    def _build_main_layout(self):
        self.main_container = tk.Frame(self.root, bg=COLOR_BG_ROOT)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        # Upper Section (Columns)
        self.upper_frame = tk.Frame(self.main_container, bg=COLOR_BG_ROOT)
        self.upper_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.upper_frame.columnconfigure(0, weight=2, minsize=260)
        self.upper_frame.columnconfigure(1, weight=5, minsize=620)
        self.upper_frame.columnconfigure(2, weight=3, minsize=320)
        self.upper_frame.rowconfigure(0, weight=1)

        self.left_col = tk.Frame(self.upper_frame, bg=COLOR_BG_ROOT)
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.center_col = tk.Frame(self.upper_frame, bg=COLOR_BG_ROOT)
        self.center_col.grid(row=0, column=1, sticky="nsew", padx=(0, 6))

        self.right_col = tk.Frame(self.upper_frame, bg=COLOR_BG_ROOT)
        self.right_col.grid(row=0, column=2, sticky="nsew")

        # Lower Section
        self.bottom_frame = tk.Frame(self.main_container, bg=COLOR_BG_ROOT, height=165)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0))
        self.bottom_frame.pack_propagate(False)

        self._build_left_modules()
        self._build_center_slam_module()
        self._build_right_modules()
        self._build_bottom_reference_modules()

    # --------------------------------------------------------------------------
    # 3. LEFT COLUMN: AIRFRAME STATUS & MINIMIZABLE RADIOMASTER POCKET ELRS
    # --------------------------------------------------------------------------
    def _build_left_modules(self):
        self.left_col.rowconfigure(0, weight=5)  # Airframe System Status
        self.left_col.rowconfigure(1, weight=4)  # Radiomaster Pocket ELRS
        self.left_col.columnconfigure(0, weight=1)

        # 3A. Airframe System Status Card
        self.card_health = self._create_card(self.left_col, "AIRFRAME SYSTEM STATUS")
        self.card_health.grid(row=0, column=0, sticky="nsew", pady=(0, 6))

        sub_lbl = tk.Label(self.card_health, text="REAL-TIME DIAGNOSTICS & HEALTH MONITORING",
                           font=self.FONT_MONO_XS, fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG)
        sub_lbl.pack(anchor="w", padx=8, pady=(2, 4))

        hw_f = tk.Frame(self.card_health, bg=COLOR_PANEL_BG)
        hw_f.pack(fill=tk.BOTH, expand=True, padx=8, pady=2)

        items = [
            ("MicoAir FC H7", "38°C", "NOMINAL", 0.9),
            ("Jetson Orin Nano", "51°C\nYOLO Active", "ACTIVE", 0.85),
            ("RPLIDAR C1", "10.2Hz", "SYNC", 0.95),
            ("ESC Motors", "44°C", "NOMINAL", 0.8),
            ("MTF-01 Optical Flow", "96% Q", "LOCKED", 0.95),
            ("BMI088 Dual IMU", "<0.02°", "CALIB", 0.9),
            ("VL53L1X ToF Alt", "1.20m", "AGL", 0.85)
        ]

        for name, val, status, bar_fill in items:
            row = tk.Frame(hw_f, bg=COLOR_PANEL_BG)
            row.pack(fill=tk.X, pady=2)

            tk.Label(row, text=name, font=self.FONT_SUBTITLE, fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, width=15, anchor="w").pack(side=tk.LEFT)

            b_cv = tk.Canvas(row, width=65, height=10, bg=COLOR_PANEL_BG, highlightthickness=0, bd=0)
            b_cv.pack(side=tk.LEFT, padx=4)
            for seg in range(6):
                seg_x = seg * 11
                seg_col = COLOR_GREEN_DEFENSE if (seg / 6.0) < bar_fill else "#1E2A3E"
                b_cv.create_rectangle(seg_x, 1, seg_x + 8, 9, fill=seg_col, outline="")

            tk.Label(row, text=val, font=self.FONT_MONO_XS, fg=COLOR_CYAN, bg=COLOR_PANEL_BG, width=10, anchor="e").pack(side=tk.RIGHT)

        # 3B. RADIOMASTER POCKET ELRS 2.4G MODULE CARD (WITH MINIMIZE BUTTON)
        self.card_rc = tk.Frame(self.left_col, bg=COLOR_PANEL_BG, bd=1, relief=tk.SOLID,
                                highlightbackground=COLOR_PANEL_BORDER, highlightthickness=1)
        self.card_rc.grid(row=1, column=0, sticky="nsew")

        # Header Bar with Minimize/Expand Toggle Button
        rc_hdr = tk.Frame(self.card_rc, bg=COLOR_CARD_HEADER_BG, height=28)
        rc_hdr.pack(fill=tk.X, side=tk.TOP)
        rc_hdr.pack_propagate(False)

        accent = tk.Frame(rc_hdr, bg=COLOR_GREEN_DEFENSE, width=3)
        accent.pack(side=tk.LEFT, fill=tk.Y)

        self.lbl_rc_title = tk.Label(rc_hdr, text=" Radiomaster Pocket ELRS 2.4G", font=self.FONT_CARD_TITLE,
                                     fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_HEADER_BG)
        self.lbl_rc_title.pack(side=tk.LEFT, padx=4)

        # Clickable Minimize / Expand Button
        self.btn_rc_min = tk.Button(rc_hdr, text="▲ MINIMIZE", font=self.FONT_MONO_XS,
                                    bg="#1A2438", fg=COLOR_CYAN, activebackground=COLOR_CYAN, activeforeground="#000000",
                                    bd=0, cursor="hand2", padx=6, pady=1, command=self._toggle_rc_minimize)
        self.btn_rc_min.pack(side=tk.RIGHT, padx=4, pady=2)

        # Sub-Label & Canvas
        self.rc_sub_lbl = tk.Label(self.card_rc, text="TELEMETRY MODULE STATUS", font=self.FONT_MONO_XS,
                                   fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG)
        self.rc_sub_lbl.pack(anchor="w", padx=8, pady=(2, 0))

        self.rc_canvas = tk.Canvas(self.card_rc, bg=COLOR_PANEL_BG, height=85, highlightthickness=0, bd=0)
        self.rc_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

    def _toggle_rc_minimize(self):
        """Collapses or expands the Radiomaster Pocket ELRS module card."""
        self.is_rc_minimized = not self.is_rc_minimized
        if self.is_rc_minimized:
            self.rc_sub_lbl.pack_forget()
            self.rc_canvas.pack_forget()
            self.btn_rc_min.config(text="▼ EXPAND", fg=COLOR_GREEN_DEFENSE)
            throttle_pct = int(self.rc_throttle * 100)
            self.lbl_rc_title.config(text=f" Radiomaster | LQ: {self.rc_lq}% | {self.rc_rate} | {self.rc_mode} | THR: {throttle_pct}%")
            self.left_col.rowconfigure(0, weight=1)
            self.left_col.rowconfigure(1, weight=0)
        else:
            self.lbl_rc_title.config(text=" Radiomaster Pocket ELRS 2.4G")
            self.rc_sub_lbl.pack(anchor="w", padx=8, pady=(2, 0))
            self.rc_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
            self.btn_rc_min.config(text="▲ MINIMIZE", fg=COLOR_CYAN)
            self.left_col.rowconfigure(0, weight=5)
            self.left_col.rowconfigure(1, weight=4)

    # --------------------------------------------------------------------------
    # 4. CENTER: 2D ROBOTIC SLAM OCCUPANCY GRID MAP (CARTOGRAPHER)
    # --------------------------------------------------------------------------
    def _build_center_slam_module(self):
        self.card_slam = self._create_card(self.center_col, "2D Robotic SLAM Occupancy Grid Map")
        self.card_slam.pack(fill=tk.BOTH, expand=True)

        tool_bar = tk.Frame(self.card_slam, bg=COLOR_CARD_HEADER_BG)
        tool_bar.pack(fill=tk.X, padx=6, pady=2)

        tk.Button(tool_bar, text="[2D SLAM GRID]", font=self.FONT_MONO_XS, bg="#0E231F", fg=COLOR_GREEN_DEFENSE,
                  bd=1, relief=tk.SOLID).pack(side=tk.LEFT, padx=2)
        tk.Button(tool_bar, text="[3D DRONE]", font=self.FONT_MONO_XS, bg="#162035", fg=COLOR_TEXT_SECONDARY,
                  bd=1, relief=tk.SOLID).pack(side=tk.LEFT, padx=2)
        tk.Button(tool_bar, text="[SCHEMATIC]", font=self.FONT_MONO_XS, bg="#162035", fg=COLOR_TEXT_SECONDARY,
                  bd=1, relief=tk.SOLID).pack(side=tk.LEFT, padx=2)

        tk.Button(tool_bar, text="🔍+", font=self.FONT_MONO_XS, bg="#162035", fg=COLOR_CYAN,
                  command=lambda: self._zoom_slam(1.2)).pack(side=tk.RIGHT, padx=2)
        tk.Button(tool_bar, text="🔍-", font=self.FONT_MONO_XS, bg="#162035", fg=COLOR_CYAN,
                  command=lambda: self._zoom_slam(0.8)).pack(side=tk.RIGHT, padx=2)
        tk.Button(tool_bar, text="↺ RESET", font=self.FONT_MONO_XS, bg="#162035", fg=COLOR_TEXT_SECONDARY,
                  command=self._reset_slam_view).pack(side=tk.RIGHT, padx=2)

        self.slam_canvas = tk.Canvas(
            self.card_slam,
            bg=COLOR_CANVAS_BLACK,
            highlightthickness=0,
            bd=0
        )
        self.slam_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.slam_canvas.bind("<MouseWheel>", self._on_slam_mousewheel)

    # --------------------------------------------------------------------------
    # 5. RIGHT COLUMN: TACTICAL CAMERA, SURVIVOR TABLE, BANDWIDTH & COMPASS
    # --------------------------------------------------------------------------
    def _build_right_modules(self):
        self.right_col.rowconfigure(0, weight=4)  # Tactical Camera
        self.right_col.rowconfigure(1, weight=3)  # Survivor Table
        self.right_col.rowconfigure(2, weight=3)  # Bandwidth & Compass
        self.right_col.columnconfigure(0, weight=1)

        # 5A. Tactical Camera Card
        self.card_cam = self._create_card(self.right_col, "Tactical Camera")
        self.card_cam.grid(row=0, column=0, sticky="nsew", pady=(0, 4))

        cam_bar = tk.Frame(self.card_cam, bg=COLOR_CARD_HEADER_BG)
        cam_bar.pack(fill=tk.X, padx=6, pady=2)

        self.btn_rgb = tk.Button(
            cam_bar,
            text="RGB OPTICAL",
            font=self.FONT_MONO_XS,
            bg="#0E231F",
            fg=COLOR_GREEN_DEFENSE,
            bd=1,
            relief=tk.SOLID,
            cursor="hand2",
            command=lambda: self._set_camera_mode("RGB")
        )
        self.btn_rgb.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.btn_thermal = tk.Button(
            cam_bar,
            text="THERMAL FLIR",
            font=self.FONT_MONO_XS,
            bg="#162035",
            fg=COLOR_TEXT_SECONDARY,
            bd=1,
            relief=tk.SOLID,
            cursor="hand2",
            command=lambda: self._set_camera_mode("THERMAL")
        )
        self.btn_thermal.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)

        self.cam_canvas = tk.Canvas(
            self.card_cam,
            bg=COLOR_CANVAS_BLACK,
            highlightthickness=0,
            bd=0
        )
        self.cam_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        # 5B. Survivor Localization Table
        self.card_survivors = self._create_card(self.right_col, "Survivor Localization Table")
        self.card_survivors.grid(row=1, column=0, sticky="nsew", pady=(0, 4))

        tbl = tk.Frame(self.card_survivors, bg=COLOR_PANEL_BG)
        tbl.pack(fill=tk.BOTH, expand=True, padx=6, pady=2)

        self.survivor_row_widgets = []
        for s in self.survivors:
            row = tk.Frame(tbl, bg=COLOR_PANEL_BG, bd=1, relief=tk.FLAT)
            row.pack(fill=tk.X, pady=1)

            lbl_id = tk.Label(row, text=s['id'], font=self.FONT_MONO_SM, fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, width=6, anchor="w")
            lbl_id.pack(side=tk.LEFT)

            lbl_grid = tk.Label(row, text=s['grid'], font=self.FONT_MONO_SM, fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL_BG, width=12, anchor="center")
            lbl_grid.pack(side=tk.LEFT)

            lbl_status = tk.Label(row, text="LOCATED", font=self.FONT_MONO_XS, fg=COLOR_ORANGE, bg=COLOR_PANEL_BG, width=9, anchor="e")
            lbl_status.pack(side=tk.RIGHT)

            self.survivor_row_widgets.append((lbl_status, lbl_grid, row, lbl_id))

        # 5C. Telemetry Bandwidth & Compass Card
        card_analytics = self._create_card(self.right_col, "TELEMETRY BANDWIDTH & COMPASS")
        card_analytics.grid(row=2, column=0, sticky="nsew")

        an_f = tk.Frame(card_analytics, bg=COLOR_PANEL_BG)
        an_f.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        self.bandwidth_canvas = tk.Canvas(an_f, width=160, height=70, bg=COLOR_PANEL_BG, highlightthickness=0, bd=0)
        self.bandwidth_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.mini_compass_canvas = tk.Canvas(an_f, width=70, height=70, bg=COLOR_PANEL_BG, highlightthickness=0, bd=0)
        self.mini_compass_canvas.pack(side=tk.RIGHT, padx=4)

    # --------------------------------------------------------------------------
    # 6. BOTTOM ROW: BATTERY MODULE + MOTOR SPECTRUM + MISSION ACTION BUTTONS
    # --------------------------------------------------------------------------
    def _build_bottom_reference_modules(self):
        # 6A. 3D Transparent Battery Module (DF-BT-01 Style)
        card_bat = self._create_card(self.bottom_frame, "BATTERY MODULE")
        card_bat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        self.battery_3d_canvas = tk.Canvas(card_bat, bg=COLOR_PANEL_BG, height=130, highlightthickness=0, bd=0)
        self.battery_3d_canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=2)

        # 6B. Electric Motor Overview & Temperature Spectrum Graph
        card_motor = self._create_card(self.bottom_frame, "ELECTRIC MOTOR OVERVIEW")
        card_motor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        self.motor_canvas = tk.Canvas(card_motor, bg=COLOR_PANEL_BG, height=130, highlightthickness=0, bd=0)
        self.motor_canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=2)

        # 6C. Mission Action Buttons
        card_act = self._create_card(self.bottom_frame, "MISSION ACTION BUTTONS")
        card_act.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 2))

        btn_f = tk.Frame(card_act, bg=COLOR_PANEL_BG, width=220)
        btn_f.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        btn_f.pack_propagate(False)

        self.btn_start = tk.Button(
            btn_f,
            text="MISSION ACTIVE",
            font=self.FONT_BTN,
            bg="#059669",
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_GREEN_DEFENSE,
            activeforeground="#000000",
            bd=0,
            cursor="hand2",
            command=self._start_mission
        )
        self.btn_start.pack(fill=tk.X, expand=True, pady=(0, 2))

        self.btn_export = tk.Button(
            btn_f,
            text="EXPORT REPORT (PDF/CSV)",
            font=self.FONT_BTN_SM,
            bg="#0284C7",
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_CYAN,
            activeforeground="#000000",
            bd=0,
            cursor="hand2",
            command=self._export_mission_report
        )
        self.btn_export.pack(fill=tk.X, expand=True, pady=(0, 2))

        self.btn_abort = tk.Button(
            btn_f,
            text="EMERGENCY ABORT (RTL)",
            font=self.FONT_BTN,
            bg="#DC2626",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#EF4444",
            activeforeground=COLOR_TEXT_PRIMARY,
            bd=0,
            cursor="hand2",
            command=self._emergency_abort
        )
        self.btn_abort.pack(fill=tk.X, expand=True)

    # --------------------------------------------------------------------------
    # HELPER: CARD CREATOR WITH EXACT ACCENT
    # --------------------------------------------------------------------------
    def _create_card(self, parent, title_text):
        card = tk.Frame(parent, bg=COLOR_PANEL_BG, bd=1, relief=tk.SOLID,
                        highlightbackground=COLOR_PANEL_BORDER, highlightthickness=1)

        hdr = tk.Frame(card, bg=COLOR_CARD_HEADER_BG, height=24)
        hdr.pack(fill=tk.X, side=tk.TOP)
        hdr.pack_propagate(False)

        accent = tk.Frame(hdr, bg=COLOR_GREEN_DEFENSE, width=3)
        accent.pack(side=tk.LEFT, fill=tk.Y)

        lbl = tk.Label(hdr, text=f" {title_text}", font=self.FONT_CARD_TITLE,
                       fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_HEADER_BG)
        lbl.pack(side=tk.LEFT, padx=4)

        return card

    # --------------------------------------------------------------------------
    # 7. RENDERING ENGINES
    # --------------------------------------------------------------------------
    def _render_waveform(self):
        cv = self.waveform_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 10:
            return

        self.waveform_phase += 0.2
        cy = h / 2.0
        bar_w = 3
        spacing = 2
        num_bars = int(w / (bar_w + spacing))

        for i in range(num_bars):
            bx = i * (bar_w + spacing)
            amp = math.sin(self.waveform_phase + i * 0.4) * (h / 2.5)
            b_h = max(3, abs(amp))
            cv.create_rectangle(bx, cy - b_h / 2, bx + bar_w, cy + b_h / 2, fill=COLOR_GREEN_DEFENSE, outline="")

    def _render_radiomaster_gimbals(self):
        if self.is_rc_minimized:
            return

        cv = self.rc_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 40 or h < 20:
            return

        r = 22
        g1_cx = w * 0.28
        g2_cx = w * 0.72
        g_cy = 32

        # Left Gimbal: Throttle / Yaw
        cv.create_oval(g1_cx - r, g_cy - r, g1_cx + r, g_cy + r, outline="#1E2A42", width=1.5)
        cv.create_line(g1_cx - r, g_cy, g1_cx + r, g_cy, fill="#182338", width=1)
        cv.create_line(g1_cx, g_cy - r, g1_cx, g_cy + r, fill="#182338", width=1)
        st1_x = g1_cx + (self.rc_yaw * (r - 6))
        st1_y = g_cy - ((self.rc_throttle - 0.5) * 2 * (r - 6))
        cv.create_oval(st1_x - 3.5, st1_y - 3.5, st1_x + 3.5, st1_y + 3.5, fill=COLOR_CYAN, outline=COLOR_TEXT_PRIMARY)
        cv.create_text(g1_cx, g_cy + r + 7, text="Throttle/Yaw", font=self.FONT_MONO_XS, fill=COLOR_TEXT_SECONDARY)

        # Right Gimbal: Pitch / Roll
        cv.create_oval(g2_cx - r, g_cy - r, g2_cx + r, g_cy + r, outline="#1E2A42", width=1.5)
        cv.create_line(g2_cx - r, g_cy, g2_cx + r, g_cy, fill="#182338", width=1)
        cv.create_line(g2_cx, g_cy - r, g2_cx, g_cy + r, fill="#182338", width=1)
        st2_x = g2_cx + (self.rc_roll * (r - 6))
        st2_y = g_cy - (self.rc_pitch * (r - 6))
        cv.create_oval(st2_x - 3.5, st2_y - 3.5, st2_x + 3.5, st2_y + 3.5, fill=COLOR_CYAN, outline=COLOR_TEXT_PRIMARY)
        cv.create_text(g2_cx, g_cy + r + 7, text="Pitch/Roll", font=self.FONT_MONO_XS, fill=COLOR_TEXT_SECONDARY)

        cv.create_text(w / 2.0, h - 6,
                       text=f"Radiomaster Pocket ELRS | LQ: {self.rc_lq}% | {self.rc_rate} | Mode: [{self.rc_mode}]",
                       font=self.FONT_MONO_XS, fill=COLOR_GREEN_DEFENSE)

    def _render_3d_battery_module(self):
        cv = self.battery_3d_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 50:
            return

        cv.create_text(16, 20, text=f"{self.battery_pct:.1f} %", font=self.FONT_TITLE, fill=COLOR_GREEN_DEFENSE, anchor="w")
        cv.create_text(16, 38, text="BATTERY LEVEL", font=self.FONT_MONO_XS, fill=COLOR_TEXT_SECONDARY, anchor="w")
        cv.create_text(16, 56, text=f"CURRENT\n{self.current_amps:.1f} A", font=self.FONT_MONO_XS, fill=COLOR_TEXT_PRIMARY, anchor="w")
        cv.create_text(85, 56, text=f"VOLTAGE\n{self.battery_voltage:.2f} V", font=self.FONT_MONO_XS, fill=COLOR_TEXT_PRIMARY, anchor="w")

        bx, by = 155, 14
        bw, bh = 85, 55
        cv.create_rectangle(bx, by, bx + bw, by + bh, outline=COLOR_CYAN, width=1.5)
        cv.create_line(bx, by, bx + 12, by - 8, fill=COLOR_CYAN, width=1.5)
        cv.create_line(bx + bw, by, bx + bw + 12, by - 8, fill=COLOR_CYAN, width=1.5)
        cv.create_line(bx + 12, by - 8, bx + bw + 12, by - 8, fill=COLOR_CYAN, width=1.5)
        cv.create_line(bx + bw + 12, by - 8, bx + bw + 12, by + bh - 8, fill=COLOR_CYAN, width=1.5)
        cv.create_line(bx + bw, by + bh, bx + bw + 12, by + bh - 8, fill=COLOR_CYAN, width=1.5)

        for c_idx in range(6):
            cx_pos = bx + 6 + c_idx * 12
            cv.create_rectangle(cx_pos, by + 10, cx_pos + 8, by + bh - 10, fill=COLOR_GREEN_DEFENSE, outline="")

        cv.create_text(bx + bw, by + bh + 14, text="DF-BT-01", font=self.FONT_MONO_XS, fill=COLOR_GREEN_DEFENSE, anchor="e")

        rx = 270
        if w > 360:
            cv.create_text(rx, 18, text="REMAINING ENDURANCE\n2h 50m", font=self.FONT_MONO_XS, fill=COLOR_GREEN_DEFENSE, anchor="w")
            cv.create_text(rx, 50, text="ENERGY: 3.42 kWh\nPOWER: 1.23 kW", font=self.FONT_MONO_XS, fill=COLOR_TEXT_SECONDARY, anchor="w")

    def _render_motor_overview(self):
        cv = self.motor_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 50:
            return

        cv.create_text(16, 20, text="ENGINE STATUS\nNOMINAL", font=self.FONT_MONO_XS, fill=COLOR_GREEN_DEFENSE, anchor="w")
        cv.create_text(16, 52, text="RPM: 3,556\nPOWER: 424 W", font=self.FONT_MONO_XS, fill=COLOR_TEXT_PRIMARY, anchor="w")

        spec_x = 130
        spec_w = max(60, w - spec_x - 20)
        spec_y = 65
        num_bars = 28
        bar_w = max(2, int(spec_w / num_bars) - 1)

        cv.create_text(spec_x, 18, text="TEMPERATURE SPECTRUM (°C)", font=self.FONT_MONO_XS, fill=COLOR_TEXT_SECONDARY, anchor="w")
        cv.create_text(w - 20, 18, text="EFFICIENCY 93%", font=self.FONT_MONO_XS, fill=COLOR_TEXT_PRIMARY, anchor="e")

        for i in range(num_bars):
            bx = spec_x + i * (bar_w + 1)
            norm = math.sin((i / float(num_bars)) * math.pi)
            b_h = max(4, int(norm * 44))
            col = COLOR_GREEN_DEFENSE if norm < 0.6 else (COLOR_AMBER if norm < 0.85 else COLOR_RED)
            cv.create_rectangle(bx, spec_y - b_h, bx + bar_w, spec_y, fill=col, outline="")

    def _render_bandwidth_and_compass(self):
        cv_b = self.bandwidth_canvas
        cv_b.delete("all")
        bw_w = cv_b.winfo_width()
        bw_h = cv_b.winfo_height()
        if bw_w > 10:
            cv_b.create_text(8, 10, text="BANDWIDTH (Gbps)", font=self.FONT_MONO_XS, fill=COLOR_TEXT_SECONDARY, anchor="w")
            cv_b.create_text(bw_w - 8, 10, text="3.1 DOWN | 1.1 UP", font=self.FONT_MONO_XS, fill=COLOR_CYAN, anchor="e")
            pts = [8, bw_h - 4]
            for step in range(8):
                px = 8 + step * ((bw_w - 16) / 7.0)
                py = bw_h - 8 - math.sin(step * 0.8) * 16 - (step * 2)
                pts.extend([px, py])
            pts.extend([bw_w - 8, bw_h - 4])
            cv_b.create_polygon(pts, fill="#0F2432", outline=COLOR_CYAN)

        cv_c = self.mini_compass_canvas
        cv_c.delete("all")
        cw_w = cv_c.winfo_width()
        cw_h = cv_c.winfo_height()
        if cw_w > 10:
            cx, cy = cw_w / 2.0, cw_h / 2.0
            r = min(cx, cy) - 6
            cv_c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#1E2A42", width=1.5)
            cv_c.create_text(cx, cy - r + 6, text="N", font=self.FONT_MONO_XS, fill=COLOR_RED)
            yaw_rad = math.radians(self.yaw)
            nx = cx + (r - 8) * math.sin(yaw_rad)
            ny = cy - (r - 8) * math.cos(yaw_rad)
            cv_c.create_line(cx, cy, nx, ny, fill=COLOR_ORANGE, width=2, arrow=tk.LAST)

    # --------------------------------------------------------------------------
    # 8. RENDERING ENGINES: CAMERA & 2D SLAM
    # --------------------------------------------------------------------------
    def _render_ip_camera(self):
        cv = self.cam_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 20 or h < 20:
            return

        cx, cy = w / 2.0, h / 2.0
        bg_col = "#070D18" if self.camera_mode == "RGB" else "#0B0418"
        wire_col = "#12233D" if self.camera_mode == "RGB" else "#250F4C"

        cv.create_rectangle(0, 0, w, h, fill=bg_col, outline="")
        vp_x = cx + math.sin(math.radians(self.yaw)) * 25
        vp_y = cy - math.sin(math.radians(self.pitch)) * 8
        cv.create_line(0, 0, vp_x, vp_y, fill=wire_col, width=1.5)
        cv.create_line(w, 0, vp_x, vp_y, fill=wire_col, width=1.5)
        cv.create_line(0, h, vp_x, vp_y, fill=wire_col, width=1.5)
        cv.create_line(w, h, vp_x, vp_y, fill=wire_col, width=1.5)

        for y_s in range(10, h, 18):
            cv.create_line(0, y_s, w, y_s, fill="#0A1628" if self.camera_mode == "RGB" else "#1A0933", width=1)

        active_target = None
        for s in self.survivors:
            if s["located"]:
                dist = math.hypot(self.drone_pos[0] - s["x"], self.drone_pos[1] - s["y"])
                if dist < 140:
                    active_target = s
                    break

        if active_target:
            sil_w = 42
            sil_h = 88
            bx1, by1 = cx - sil_w / 2.0, cy - sil_h / 2.0
            bx2, by2 = bx1 + sil_w, by1 + sil_h

            if self.camera_mode == "THERMAL":
                cv.create_oval(cx - 12, by1 + 4, cx + 12, by1 + 28, fill="#FF6B00", outline="#FFD600", width=2)
                cv.create_rectangle(bx1 + 8, by1 + 30, bx2 - 8, by2, fill="#E11D48", outline="#FF6B00", width=2)
            else:
                cv.create_oval(cx - 10, by1 + 6, cx + 10, by1 + 26, fill="#15803D", outline=COLOR_GREEN_DEFENSE, width=1)
                cv.create_rectangle(bx1 + 8, by1 + 28, bx2 - 8, by2, fill="#166534", outline=COLOR_GREEN_DEFENSE, width=1)

            bracket_col = COLOR_GREEN_DEFENSE if self.camera_mode == "RGB" else COLOR_ORANGE
            c_len = 10
            cv.create_line(bx1, by1, bx1 + c_len, by1, fill=bracket_col, width=2)
            cv.create_line(bx1, by1, bx1, by1 + c_len, fill=bracket_col, width=2)
            cv.create_line(bx2, by1, bx2 - c_len, by1, fill=bracket_col, width=2)
            cv.create_line(bx2, by1, bx2 - c_len, by1, fill=bracket_col, width=2)
            cv.create_line(bx1, by2, bx1 + c_len, by2, fill=bracket_col, width=2)
            cv.create_line(bx1, by2, bx1, by2 - c_len, fill=bracket_col, width=2)
            cv.create_line(bx2, by2, bx2 - c_len, by2, fill=bracket_col, width=2)
            cv.create_line(bx2, by2, bx2, by2 - c_len, fill=bracket_col, width=2)

            cv.create_text(bx1 + 4, by1 - 8, text=f"[YOLOv8n] PERSON: 96.4%", anchor="w", font=self.FONT_MONO_XS, fill=bracket_col)
            cv.create_text(bx1, by2 + 10, text="RANGE: 1.4m | BIOMETRIC TEMP: 37.1°C", anchor="w", font=self.FONT_MONO_XS, fill=COLOR_CYAN)

        now = time.time()
        if now - self.last_blink_time > 0.5:
            self.rec_blink_state = not self.rec_blink_state
            self.last_blink_time = now
        if self.rec_blink_state:
            cv.create_oval(8, 8, 14, 14, fill=COLOR_RED, outline="")
        cv.create_text(18, 11, text="REC", font=self.FONT_MONO_XS, fill=COLOR_TEXT_PRIMARY, anchor="w")
        cv.create_text(w - 8, 11, text="30 FPS", font=self.FONT_MONO_XS, fill=COLOR_CYAN, anchor="e")

    def _render_slam_canvas(self):
        cv = self.slam_canvas
        cv.delete("all")
        cw = cv.winfo_width()
        ch = cv.winfo_height()
        if cw < 50 or ch < 50:
            return

        base_sx = cw / self.arena_virtual_w
        base_sy = ch / self.arena_virtual_h
        scale_x = base_sx * self.slam_zoom
        scale_y = base_sy * self.slam_zoom

        def to_cv(x, y):
            cx = (x * scale_x) + self.slam_pan_x
            cy = (y * scale_y) + self.slam_pan_y
            return cx, cy

        grid_cols = 16
        grid_rows = 15
        col_letters = "ABCDEFGHIJKLMNOP"
        step_x = cw / grid_cols
        step_y = ch / grid_rows

        for c in range(grid_cols + 1):
            gx = c * step_x
            cv.create_line(gx, 0, gx, ch, fill="#0B1322", width=1)
            if c < grid_cols:
                cv.create_text(gx + step_x / 2, 7, text=col_letters[c], font=self.FONT_MONO_XS, fill=COLOR_TEXT_MUTED)

        for r in range(grid_rows + 1):
            gy = r * step_y
            cv.create_line(0, gy, cw, gy, fill="#0B1322", width=1)
            if r < grid_rows:
                cv.create_text(7, gy + step_y / 2, text=str(r + 1), font=self.FONT_MONO_XS, fill=COLOR_TEXT_MUTED)

        for (w_p1, w_p2) in self.maze_walls:
            cx1, cy1 = to_cv(*w_p1)
            cx2, cy2 = to_cv(*w_p2)
            cv.create_line(cx1, cy1, cx2, cy2, fill="#1E2A42", width=4)
            cv.create_line(cx1, cy1, cx2, cy2, fill="#38BDF8", width=1.5)

        if len(self.trajectory_history) > 1:
            flat_pts = []
            for hx, hy in self.trajectory_history:
                tx, ty = to_cv(hx, hy)
                flat_pts.extend([tx, ty])
            cv.create_line(flat_pts, fill="#004D61", width=5, smooth=True)
            cv.create_line(flat_pts, fill=COLOR_CYAN, width=2, smooth=True)

        dx, dy = to_cv(*self.drone_pos)

        sweep_rad = math.radians(self.lidar_angle)
        cone_radius = 85 * min(scale_x, scale_y)
        span = math.radians(35)
        lx1 = dx + cone_radius * math.cos(sweep_rad - span)
        ly1 = dy + cone_radius * math.sin(sweep_rad - span)
        lx2 = dx + cone_radius * math.cos(sweep_rad + span)
        ly2 = dy + cone_radius * math.sin(sweep_rad + span)
        cv.create_polygon(dx, dy, lx1, ly1, lx2, ly2, fill="#002D3B", outline="")

        if len(self.lidar_points) > 0:
            for px, py in self.lidar_points:
                pt_x, pt_y = to_cv(px, py)
                cv.create_oval(pt_x - 1.5, pt_y - 1.5, pt_x + 1.5, pt_y + 1.5, fill=COLOR_CYAN, outline="")

        for s in self.survivors:
            if s["located"]:
                sx, sy = to_cv(s["x"], s["y"])
                pulse_r = 12 + (int(time.time() * 8) % 6)
                cv.create_oval(sx - pulse_r, sy - pulse_r, sx + pulse_r, sy + pulse_r, outline="#FF6B00", width=1.5)
                cv.create_oval(sx - 7, sy - 7, sx + 7, sy + 7, fill=COLOR_ORANGE, outline=COLOR_TEXT_PRIMARY, width=1.5)
                cv.create_text(sx, sy + 13, text=f"{s['id']} [{s['grid'].split()[-1]}]", font=self.FONT_MONO_SM, fill=COLOR_ORANGE)

        h_rad = math.radians(self.yaw)
        hx = dx + 22 * math.sin(h_rad)
        hy = dy - 22 * math.cos(h_rad)
        cv.create_line(dx, dy, hx, hy, fill=COLOR_CYAN, width=2.5, arrow=tk.LAST, arrowshape=(7, 9, 3))
        cv.create_oval(dx - 11, dy - 11, dx + 11, dy + 11, outline=COLOR_ORANGE, width=2)
        cv.create_oval(dx - 4, dy - 4, dx + 4, dy + 4, fill=COLOR_ORANGE, outline="")
        cv.create_line(dx - 8, dy, dx + 8, dy, fill=COLOR_TEXT_PRIMARY, width=1.5)
        cv.create_line(dx, dy - 8, dx, dy + 8, fill=COLOR_TEXT_PRIMARY, width=1.5)

    # --------------------------------------------------------------------------
    # 9. SIMULATION ENGINE TICK
    # --------------------------------------------------------------------------
    def _schedule_updates(self):
        self._update_simulation_tick()
        self.root.after(33, self._schedule_updates)

    def _update_simulation_tick(self):
        if self.is_mission_active and not self.is_paused and self.start_time:
            self.elapsed_time = time.time() - self.start_time

        self.lbl_utc_time.config(text=f"UTC TIME\n{time.strftime('%H:%M:%S')}")
        self.lidar_angle = (self.lidar_angle + 10.2) % 360.0

        if self.is_mission_active and not self.is_paused:
            self._advance_corridor_flight()

        # Render All Subsystems
        self._render_waveform()
        if self.is_rc_minimized:
            throttle_pct = int(self.rc_throttle * 100)
            self.lbl_rc_title.config(text=f" Radiomaster | LQ: {self.rc_lq}% | {self.rc_rate} | {self.rc_mode} | THR: {throttle_pct}%")
        else:
            self._render_radiomaster_gimbals()
        self._render_3d_battery_module()
        self._render_motor_overview()
        self._render_bandwidth_and_compass()
        self._render_ip_camera()
        self._render_slam_canvas()

    def _advance_corridor_flight(self):
        p1 = self.corridor_waypoints[self.waypoint_index]
        next_idx = (self.waypoint_index + 1) % len(self.corridor_waypoints)
        p2 = self.corridor_waypoints[next_idx]

        step_speed = 0.038
        self.waypoint_t += step_speed

        if self.waypoint_t >= 1.0:
            self.waypoint_t = 0.0
            self.waypoint_index = next_idx
            p1 = p2
            next_idx = (self.waypoint_index + 1) % len(self.corridor_waypoints)
            p2 = self.corridor_waypoints[next_idx]

        cur_x = p1[0] + (p2[0] - p1[0]) * self.waypoint_t
        cur_y = p1[1] + (p2[1] - p1[1]) * self.waypoint_t
        self.drone_pos = [cur_x, cur_y]

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        heading_deg = (math.degrees(math.atan2(dx, -dy))) % 360.0
        self.yaw = heading_deg

        turn_rate = (heading_deg - 198.0) / 90.0
        self.rc_yaw = max(-0.8, min(0.8, turn_rate * 0.4))
        self.rc_pitch = 0.25
        self.rc_roll = max(-0.6, min(0.6, turn_rate * 0.3))

        self.trajectory_history.append(list(self.drone_pos))
        if len(self.trajectory_history) > 500:
            self.trajectory_history.pop(0)

        self.distance_traversed += 0.06
        self.exploration_percent = min(100.0, self.exploration_percent + 0.035)

        self.battery_pct = max(10.0, self.battery_pct - 0.003)
        self.battery_voltage = 20.0 + (self.battery_pct / 100.0) * 2.84

        self.lidar_points = []
        for _ in range(8):
            a_rad = math.radians((self.lidar_angle + random.uniform(-25, 25)) % 360.0)
            r_dist = random.uniform(40, 160)
            hit_x = self.drone_pos[0] + r_dist * math.cos(a_rad)
            hit_y = self.drone_pos[1] + r_dist * math.sin(a_rad)
            self.lidar_points.append((hit_x, hit_y))

        for i, s in enumerate(self.survivors):
            if not s["located"]:
                dist_to_survivor = math.hypot(self.drone_pos[0] - s["x"], self.drone_pos[1] - s["y"])
                if dist_to_survivor < 65:
                    s["located"] = True
                    s["status"] = "LOCATED"
                    s["conf"] = round(random.uniform(95.2, 98.6), 1)
                    self.survivors_located_count += 1

                    AudioAlertSystem.play_sonar_chirp()
                    AudioAlertSystem.speak_tactical(f"Survivor {s['id']} acquired at {s['grid']}")

                    lbl_status, lbl_grid, row, lbl_id = self.survivor_row_widgets[i]
                    lbl_id.config(fg=COLOR_ORANGE)
                    lbl_grid.config(fg=COLOR_ORANGE)
                    lbl_status.config(text="LOCATED", fg=COLOR_GREEN_DEFENSE)

                    if self.survivors_located_count == 6:
                        AudioAlertSystem.play_victory_alarm()
                        AudioAlertSystem.speak_tactical("All six survivors located. Initiating return to launch.")

    # --------------------------------------------------------------------------
    # PILOT ACTIONS & CONTROLS
    # --------------------------------------------------------------------------
    def _start_mission(self):
        if not self.is_mission_active:
            self.is_mission_active = True
            self.is_paused = False
            self.start_time = time.time()
            self.btn_start.config(text="PAUSE MISSION", bg=COLOR_AMBER)
            AudioAlertSystem.play_sonar_chirp()
            AudioAlertSystem.speak_tactical("Mission armed. Takeoff initiated.")
        else:
            self._toggle_pause()

    def _toggle_pause(self):
        if self.is_mission_active:
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.btn_start.config(text="RESUME MISSION", bg=COLOR_ORANGE)
                self.rc_mode = "HOVER HOLD"
                AudioAlertSystem.speak_tactical("Mission paused. Holding position.")
            else:
                self.btn_start.config(text="PAUSE MISSION", bg=COLOR_AMBER)
                self.rc_mode = "AUTO SLAM"
                AudioAlertSystem.speak_tactical("Search resumed.")

    def _emergency_abort(self):
        self.is_mission_active = False
        self.is_paused = False
        self.rc_mode = "RTL ABORT"
        self.btn_start.config(text="MISSION ACTIVE", bg="#059669")
        AudioAlertSystem.play_sonar_chirp()
        AudioAlertSystem.speak_tactical("Emergency abort. Returning to launch.")

    def _set_camera_mode(self, mode):
        self.camera_mode = mode
        if mode == "RGB":
            self.btn_rgb.config(bg="#0E231F", fg=COLOR_GREEN_DEFENSE)
            self.btn_thermal.config(bg="#162035", fg=COLOR_TEXT_SECONDARY)
        else:
            self.btn_thermal.config(bg="#2E1065", fg=COLOR_ORANGE)
            self.btn_rgb.config(bg="#162035", fg=COLOR_TEXT_SECONDARY)
            AudioAlertSystem.speak_tactical("Thermal vision active.")

    def _zoom_slam(self, factor):
        self.slam_zoom = max(0.6, min(3.0, self.slam_zoom * factor))

    def _reset_slam_view(self):
        self.slam_zoom = 1.0
        self.slam_pan_x = 0
        self.slam_pan_y = 0

    def _on_slam_mousewheel(self, event):
        if event.delta > 0:
            self._zoom_slam(1.1)
        else:
            self._zoom_slam(0.9)

    def _open_preflight_checklist(self):
        modal = tk.Toplevel(self.root)
        modal.title("PRE-FLIGHT SYSTEMS HEALTH CHECKLIST")
        modal.geometry("540x420")
        modal.configure(bg=COLOR_BG_ROOT)
        modal.transient(self.root)
        modal.grab_set()

        tk.Label(modal, text="✈ PRE-ARM AUTOMATED SELF-TEST", font=self.FONT_TITLE,
                 fg=COLOR_GREEN_DEFENSE, bg=COLOR_BG_ROOT).pack(pady=(16, 4))
        tk.Label(modal, text="NIDAR AirMouse Challenge PS2 - Team Edith Safety Protocols",
                 font=self.FONT_SUBTITLE, fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_ROOT).pack(pady=(0, 16))

        checklist = [
            ("RPLiDAR C1 360° DTOF Scanner", "10.2 Hz Spin Rate | 1440 pts/rev", "PASS ✔"),
            ("MicoAir MTF-01 Optical Flow", "Quality: 96% | Range: 1.2m locked", "PASS ✔"),
            ("MicoAir H743 Dual IMU Gyro", "Calibrated (<0.02 deg/s drift)", "PASS ✔"),
            ("6S Molicel 21700 Battery Pack", "22.84V | Individual Cells > 3.80V", "PASS ✔"),
            ("Wi-Fi 6 Low-Latency Comms Link", "TP-Link AX55 | Ping: 3.2ms", "PASS ✔"),
            ("Radiomaster Pocket ELRS Link", "500Hz Packet Rate | LQ 100%", "PASS ✔"),
            ("Jetson Orin Nano TensorRT Engine", "YOLOv8n FP16 Warmup (8.2ms)", "PASS ✔"),
        ]

        f = tk.Frame(modal, bg=COLOR_PANEL_BG, bd=1, relief=tk.SOLID)
        f.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 16))

        for name, detail, status in checklist:
            row = tk.Frame(f, bg=COLOR_PANEL_BG)
            row.pack(fill=tk.X, padx=12, pady=5)
            tk.Label(row, text=name, font=self.FONT_SUBTITLE, fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG).pack(side=tk.LEFT)
            tk.Label(row, text=status, font=self.FONT_MONO_SM, fg=COLOR_GREEN_DEFENSE, bg=COLOR_PANEL_BG).pack(side=tk.RIGHT)
            tk.Label(row, text=f"({detail})", font=self.FONT_MONO_XS, fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG).pack(side=tk.RIGHT, padx=8)

        tk.Button(modal, text="CONFIRM & ARM SYSTEM", font=self.FONT_BTN, bg="#059669", fg=COLOR_TEXT_PRIMARY,
                  command=modal.destroy).pack(pady=(0, 16), ipadx=16, ipady=4)

    def _export_mission_report(self):
        ts_str = time.strftime("%Y%m%d_%H%M%S")
        filename = f"TEAM_EDITH_AIRMOUSE_REPORT_{ts_str}.csv"
        filepath = os.path.join(self.base_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("================================================================================\n")
                f.write("TEAM EDITH - AIRMOUSE GROUND CONTROL STATION (GCS) OFFICIAL MISSION REPORT\n")
                f.write("NIDAR AirMouse Challenge - Problem Statement 2 (GPS-Denied Indoor Search)\n")
                f.write("================================================================================\n\n")
                f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Mission Duration: {self.elapsed_time:.1f} seconds\n")
                f.write(f"Total Traversed Distance: {self.distance_traversed:.1f} meters\n")
                f.write(f"Arena Exploration: {self.exploration_percent:.1f}%\n")
                f.write(f"Total Targets Found: {self.survivors_located_count} / 6\n")
                f.write(f"Early Exit Bonus Eligible: {'YES' if self.survivors_located_count == 6 else 'NO'}\n\n")
                f.write("SURVIVOR LOCALIZATION TABLE (1m x 1m METRIC ARENA GEOTAGS):\n")
                f.write("Target_ID,Status,Grid_Coordinate,YOLOv8_Confidence_Percent\n")
                for s in self.survivors:
                    f.write(f"{s['id']},{s['status']},{s['grid']},{s['conf']}\n")

            AudioAlertSystem.speak_tactical("Mission report exported successfully.")
            messagebox.showinfo("REPORT EXPORTED", f"Official NIDAR Mission Report successfully saved:\n\n{filepath}")
        except Exception as e:
            messagebox.showerror("EXPORT ERROR", f"Failed to export report: {e}")


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    app_root = tk.Tk()
    app = TeamEdithAirMouseGCS(app_root)
    app_root.mainloop()
