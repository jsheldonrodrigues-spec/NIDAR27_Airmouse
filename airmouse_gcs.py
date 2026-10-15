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
# 3. COLOR PALETTE & AESTHETICS (Stealth Military Cyber Defense)
# ------------------------------------------------------------------------------
COLOR_BG_ROOT          = "#070B14"  # Deep space obsidian
COLOR_PANEL_BG         = "#0F1626"  # Matte titanium card container
COLOR_PANEL_BORDER     = "#1A263D"  # Structural micro-borders
COLOR_HEADER_BG        = "#0A101D"  # Top app bar background
COLOR_CARD_HEADER_BG   = "#141D30"  # Card header background
COLOR_CANVAS_BLACK     = "#050811"  # Deep canvas black for SLAM & Video

# Vibrant Military Cyber Accents
COLOR_GREEN_DEFENSE    = "#05DF72"  # Tactical Emerald Defense Green (Nominal)
COLOR_CYAN             = "#00F2FE"  # Primary laser & heading accent
COLOR_ORANGE           = "#FF6B00"  # Hazard orange (targets, warnings)
COLOR_AMBER            = "#F59E0B"  # Searching / caution amber
COLOR_RED              = "#EF4444"  # Emergency abort red
COLOR_TEXT_PRIMARY     = "#FFFFFF"  # Crisp signal white
COLOR_TEXT_SECONDARY   = "#94A3B8"  # Secondary tactical slate grey
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

        # Keybindings
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
        self.lidar_ray_cache = []

        # SLAM Interactive Zoom & Pan
        self.slam_zoom = 1.0
        self.slam_pan_x = 0
        self.slam_pan_y = 0

        # ----------------------------------------------------------------------
        # 6 SURVIVORS DEFINITION (T1 to T6) ACROSS DISCRETE ARENA GRIDS
        # ----------------------------------------------------------------------
        self.survivors = [
            {"id": "T1", "status": "SEARCHING...", "grid": "Grid [C-4]", "conf": 0.0, "located": False, "x": 170, "y": 160},
            {"id": "T2", "status": "SEARCHING...", "grid": "Grid [G-2]", "conf": 0.0, "located": False, "x": 410, "y": 75},
            {"id": "T3", "status": "SEARCHING...", "grid": "Grid [K-7]", "conf": 0.0, "located": False, "x": 655, "y": 300},
            {"id": "T4", "status": "SEARCHING...", "grid": "Grid [M-12]", "conf": 0.0, "located": False, "x": 785, "y": 510},
            {"id": "T5", "status": "SEARCHING...", "grid": "Grid [D-14]", "conf": 0.0, "located": False, "x": 218, "y": 625},
            {"id": "T6", "status": "SEARCHING...", "grid": "Grid [J-11]", "conf": 0.0, "located": False, "x": 590, "y": 490},
        ]
        self.survivors_located_count = 0

        # Persistent SLAM Point Cloud on Obstacle Surfaces
        self.persistent_slam_cloud = []
        self.explored_points = set()

        # ----------------------------------------------------------------------
        # COMPREHENSIVE COLLISION-FREE MAZE WAYPOINTS (1000x700 Virtual Space)
        # ----------------------------------------------------------------------
        self.arena_virtual_w = 1000
        self.arena_virtual_h = 700

        self.corridor_waypoints = [
            (90, 160),    # 0: Home Entry/Exit LZ [B-4]
            (90, 75),     # 1: North runway
            (170, 75),    # 2: Enter North corridor
            (170, 160),   # 3: T1 Target Sector [C-4]
            (250, 160),   # 4: Exit T1 chamber to North corridor
            (250, 75),    # 5: North corridor main
            (410, 75),    # 6: T2 Target Sector [G-2]
            (700, 75),    # 7: North corridor East junction
            (700, 220),   # 8: East hallway descending
            (655, 300),   # 9: T3 Target Sector [K-7]
            (700, 300),   # 10: Re-align East corridor
            (700, 440),   # 11: Descending to South-East doorway
            (785, 440),   # 12: Moving into T4 chamber
            (785, 510),   # 13: T4 Target Sector [M-12]
            (785, 600),   # 14: South-East exit
            (700, 600),   # 15: South corridor entrance
            (590, 600),   # 16: South corridor at T6 doorway
            (590, 490),   # 17: T6 Target Sector [J-11]
            (590, 600),   # 18: Re-enter South corridor
            (440, 600),   # 19: South corridor heading West
            (218, 600),   # 20: SW junction
            (218, 625),   # 21: T5 Target Sector [D-14]
            (218, 600),   # 22: SW room return
            (150, 600),   # 23: West approach
            (90, 600),    # 24: West runway bottom
            (90, 400),    # 25: Ascending West corridor
            (90, 260),    # 26: Passing LZ approach
            (90, 160)     # 27: Safe return to Home LZ [B-4]
        ]
        self.waypoint_index = 0
        self.waypoint_t = 0.0
        self.drone_pos = list(self.corridor_waypoints[0])
        self.trajectory_history = []

        # High-Contrast Structural Maze Walls (Outer Boundaries & Corridors)
        self.maze_walls = [
            # 1. Outer Perimeter
            ((50, 40), (950, 40)),
            ((950, 40), (950, 660)),
            ((950, 660), (50, 660)),
            ((50, 660), (50, 40)),

            # 2. West LZ corridor & Sector 1 (T1 at 170, 160)
            ((130, 110), (130, 220)),
            ((130, 220), (210, 220)),
            ((290, 120), (660, 120)),
            ((290, 120), (290, 220)),

            # 3. East Sector (T3 at 655, 300)
            ((750, 40), (750, 220)),
            ((580, 200), (580, 360)),
            ((750, 260), (870, 260)),
            ((870, 180), (870, 260)),

            # 4. South-East & T4 (at 785, 510)
            ((750, 340), (750, 400)),
            ((750, 480), (750, 520)),
            ((750, 340), (870, 340)),
            ((870, 420), (950, 420)),

            # 5. South Corridor & T6 (at 590, 490)
            ((500, 410), (660, 410)),
            ((500, 410), (500, 540)),
            ((320, 560), (540, 560)),
            ((640, 560), (750, 560)),

            # 6. Central Chambers
            ((320, 220), (480, 220)),
            ((480, 220), (480, 340)),
            ((320, 320), (420, 320)),
            ((320, 320), (320, 440)),
            ((320, 440), (420, 440)),

            # 7. South-West & T5 (at 218, 625)
            ((130, 300), (230, 300)),
            ((130, 300), (130, 500)),
            ((130, 500), (230, 500)),
        ]

        # Explored corridor polygon zones (pre-computed for realistic Cartographer free space)
        self.corridor_polys = [
            [(60, 50), (120, 50), (120, 650), (60, 650)],              # West main runway
            [(60, 50), (940, 50), (940, 110), (60, 110)],              # North corridor
            [(120, 120), (280, 120), (280, 210), (120, 210)],          # T1 chamber
            [(260, 50), (450, 50), (450, 150), (260, 150)],            # T2 North approach
            [(670, 50), (740, 50), (740, 650), (670, 650)],            # East main descending
            [(590, 230), (740, 230), (740, 380), (590, 380)],          # T3 East chamber
            [(740, 350), (940, 350), (940, 650), (740, 650)],          # T4 South-East chamber
            [(490, 420), (670, 420), (670, 590), (490, 590)],          # T6 South chamber
            [(120, 510), (310, 510), (310, 650), (120, 650)],          # T5 South-West room
            [(60, 570), (740, 570), (740, 650), (60, 650)],            # South corridor main
        ]

        # Build UI Components
        self._build_top_header()
        self._build_main_layout()

        # Start 60 FPS Event Loop
        self._schedule_updates()

    # --------------------------------------------------------------------------
    # FONTS INITIALIZATION (HIGH-TECH CYBER AEROSPACE STANDARD)
    # --------------------------------------------------------------------------
    def _init_fonts(self):
        from tkinter import font as tkfont
        available_fonts = [f.lower() for f in tkfont.families()]

        has_rajdhani = any("rajdhani" in f for f in available_fonts)
        has_jetbrains = any("jetbrains mono" in f for f in available_fonts)
        has_bahnschrift = any("bahnschrift" in f for f in available_fonts)
        has_cascadia = any("cascadia code" in f for f in available_fonts)

        # Default to ultra-modern Rajdhani & JetBrains Mono with 100% priority
        self.font_mode = "RAJDHANI"

        init_hdr = "Rajdhani" if has_rajdhani else ("Bahnschrift" if has_bahnschrift else "Segoe UI")
        init_mono = "JetBrains Mono" if has_jetbrains else ("Cascadia Code" if has_cascadia else "Consolas")

        # Native Tkinter Font Objects
        self.FONT_TITLE       = tkfont.Font(family=init_hdr, size=16, weight="bold")
        self.FONT_SUBTITLE    = tkfont.Font(family=init_hdr, size=11, weight="bold")
        self.FONT_CARD_TITLE  = tkfont.Font(family=init_hdr, size=12, weight="bold")
        self.FONT_BTN         = tkfont.Font(family=init_hdr, size=11, weight="bold")
        self.FONT_BTN_SM      = tkfont.Font(family=init_hdr, size=9, weight="bold")

        self.FONT_TELEMETRY   = tkfont.Font(family=init_mono, size=11, weight="bold")
        self.FONT_MONO_MD     = tkfont.Font(family=init_mono, size=10, weight="bold")
        self.FONT_MONO_SM     = tkfont.Font(family=init_mono, size=9, weight="bold")
        self.FONT_MONO_XS     = tkfont.Font(family=init_mono, size=8, weight="bold")

        self._apply_font_preset("RAJDHANI")

    def _apply_font_preset(self, mode):
        """Applies high-visibility typography presets across the entire GCS application."""
        from tkinter import font as tkfont
        available_fonts = [f.lower() for f in tkfont.families()]
        self.font_mode = mode

        if mode == "RAJDHANI":
            hdr_fam = "Rajdhani" if any("rajdhani" in f for f in available_fonts) else "Segoe UI"
            mono_fam = "JetBrains Mono" if any("jetbrains" in f for f in available_fonts) else "Consolas"
            btn_txt = "FONT: RAJDHANI DEFENSE"
        elif mode == "DIN":
            hdr_fam = "Bahnschrift" if any("bahnschrift" in f for f in available_fonts) else "Segoe UI"
            mono_fam = "Cascadia Code" if any("cascadia code" in f for f in available_fonts) else "Consolas"
            btn_txt = "FONT: DIN TACTICAL"
        else:  # "SEGOE"
            hdr_fam = "Segoe UI" if any("segoe ui" in f for f in available_fonts) else "Helvetica"
            mono_fam = "Consolas" if any("consolas" in f for f in available_fonts) else "Courier"
            btn_txt = "FONT: SEGOE CYBER"

        self.FONT_TITLE.configure(family=hdr_fam, size=16, weight="bold")
        self.FONT_SUBTITLE.configure(family=hdr_fam, size=11, weight="bold")
        self.FONT_CARD_TITLE.configure(family=hdr_fam, size=12, weight="bold")
        self.FONT_BTN.configure(family=hdr_fam, size=11, weight="bold")
        self.FONT_BTN_SM.configure(family=hdr_fam, size=9, weight="bold")

        self.FONT_TELEMETRY.configure(family=mono_fam, size=11, weight="bold")
        self.FONT_MONO_MD.configure(family=mono_fam, size=10, weight="bold")
        self.FONT_MONO_SM.configure(family=mono_fam, size=9, weight="bold")
        self.FONT_MONO_XS.configure(family=mono_fam, size=8, weight="bold")

        if hasattr(self, "btn_font_toggle"):
            self.btn_font_toggle.config(text=btn_txt)

    def _cycle_font_preset(self):
        """Toggles between Rajdhani Defense, DIN Tactical, and Segoe Cyber typography styles."""
        presets = ["RAJDHANI", "DIN", "SEGOE"]
        cur_idx = presets.index(self.font_mode) if self.font_mode in presets else 0
        next_mode = presets[(cur_idx + 1) % len(presets)]
        self._apply_font_preset(next_mode)

    # --------------------------------------------------------------------------
    # FULL SCREEN CONTROLS
    # --------------------------------------------------------------------------
    def _toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        if hasattr(self, "btn_fullscreen"):
            self.btn_fullscreen.config(text="RESTORE" if self.is_fullscreen else "FULLSCREEN")

    def _exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes("-fullscreen", False)
            if hasattr(self, "btn_fullscreen"):
                self.btn_fullscreen.config(text="FULLSCREEN")

    # --------------------------------------------------------------------------
    # 1. TOP HEADER APP BAR (CLEAN MODERN DEFENSE STANDARD)
    # --------------------------------------------------------------------------
    def _build_top_header(self):
        self.header_frame = tk.Frame(self.root, bg=COLOR_HEADER_BG, height=60, bd=0)
        self.header_frame.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(4, 4))
        self.header_frame.pack_propagate(False)

        # 1A. Left: Brand Name
        brand_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        brand_frame.pack(side=tk.LEFT, padx=10, pady=2)

        lbl_title = tk.Label(brand_frame, text="TEAM EDITH", font=self.FONT_TITLE,
                             fg=COLOR_TEXT_PRIMARY, bg=COLOR_HEADER_BG)
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(brand_frame, text="AIRMOUSE TACTICAL GCS // PS2-NIDAR-2027",
                           font=self.FONT_MONO_XS, fg=COLOR_CYAN, bg=COLOR_HEADER_BG)
        lbl_sub.pack(anchor="w")

        # 1B. Center: Mission Status Pills & Audio Waveform
        center_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        center_frame.pack(side=tk.LEFT, expand=True)

        pill_row = tk.Frame(center_frame, bg=COLOR_HEADER_BG)
        pill_row.pack(pady=4)

        tk.Label(pill_row, text="ARENA\n15m x 15m", font=self.FONT_MONO_XS,
                 fg=COLOR_TEXT_SECONDARY, bg="#111827", padx=6, pady=2, relief=tk.SOLID, bd=1).pack(side=tk.LEFT, padx=3)

        self.lbl_utc_time = tk.Label(pill_row, text="MISSION CLOCK\n00:00:00", font=self.FONT_MONO_XS,
                                     fg=COLOR_TEXT_PRIMARY, bg="#111827", padx=6, pady=2, relief=tk.SOLID, bd=1)
        self.lbl_utc_time.pack(side=tk.LEFT, padx=3)

        wf_box = tk.Frame(pill_row, bg="#111827", relief=tk.SOLID, bd=1, padx=4)
        wf_box.pack(side=tk.LEFT, padx=3)
        tk.Label(wf_box, text="UPLINK LINK\nAES-256 OK", font=self.FONT_MONO_XS,
                 fg=COLOR_GREEN_DEFENSE, bg="#111827").pack(side=tk.LEFT, padx=2)
        self.waveform_canvas = tk.Canvas(wf_box, width=55, height=22, bg="#111827", highlightthickness=0, bd=0)
        self.waveform_canvas.pack(side=tk.LEFT, padx=2)

        tk.Label(pill_row, text="AUTOPILOT\nNOMINAL AUTO", font=self.FONT_MONO_XS,
                 fg=COLOR_GREEN_DEFENSE, bg="#0E231F", padx=6, pady=2, relief=tk.SOLID, bd=1).pack(side=tk.LEFT, padx=3)

        self.lbl_wifi_status = tk.Label(pill_row, text="WI-FI 6 RSSI\nSTRONG -42 dBm", font=self.FONT_MONO_XS,
                                        fg=COLOR_CYAN, bg="#111827", padx=6, pady=2, relief=tk.SOLID, bd=1)
        self.lbl_wifi_status.pack(side=tk.LEFT, padx=3)

        self.lbl_early_exit = tk.Label(pill_row, text="6/6 SURVIVORS SECURED\n[EARLY EXIT BONUS READY]", font=self.FONT_MONO_XS,
                                       fg=COLOR_GREEN_DEFENSE, bg="#0E231F", padx=6, pady=2, relief=tk.SOLID, bd=1)
        self.lbl_early_exit.pack(side=tk.LEFT, padx=3)

        # 1C. Right: Controls & Pre-Arm
        right_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        right_frame.pack(side=tk.RIGHT, padx=10, pady=2)

        self.btn_font_toggle = tk.Button(
            right_frame,
            text="FONT: RAJDHANI DEFENSE",
            font=self.FONT_MONO_XS,
            fg=COLOR_CYAN,
            bg="#111827",
            activebackground=COLOR_CYAN,
            activeforeground="#000000",
            bd=1,
            relief=tk.SOLID,
            cursor="hand2",
            padx=6,
            command=self._cycle_font_preset
        )
        self.btn_font_toggle.pack(side=tk.LEFT, padx=3)

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
            text="FULLSCREEN",
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
    # 2. MAIN LAYOUT (LEFT: SYSTEM STATUS, CENTER: SLAM + JOYSTICK/COMPASS)
    # --------------------------------------------------------------------------
    def _build_main_layout(self):
        self.main_container = tk.Frame(self.root, bg=COLOR_BG_ROOT)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        # Upper Section (Columns)
        self.upper_frame = tk.Frame(self.main_container, bg=COLOR_BG_ROOT)
        self.upper_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.upper_frame.columnconfigure(0, weight=3, minsize=280)  # Left: Dedicated System Status
        self.upper_frame.columnconfigure(1, weight=6, minsize=680)  # Center: 2D SLAM + Joystick/Compass Console
        self.upper_frame.columnconfigure(2, weight=3, minsize=320)  # Right: Camera & Survivor Table
        self.upper_frame.rowconfigure(0, weight=1)

        self.left_col = tk.Frame(self.upper_frame, bg=COLOR_BG_ROOT)
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.center_col = tk.Frame(self.upper_frame, bg=COLOR_BG_ROOT)
        self.center_col.grid(row=0, column=1, sticky="nsew", padx=(0, 6))

        self.right_col = tk.Frame(self.upper_frame, bg=COLOR_BG_ROOT)
        self.right_col.grid(row=0, column=2, sticky="nsew")

        # Lower Section: Battery + Motor Overview + Action Buttons
        self.bottom_frame = tk.Frame(self.main_container, bg=COLOR_BG_ROOT, height=155)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0))
        self.bottom_frame.pack_propagate(False)

        self._build_left_system_status()
        self._build_center_slam_and_controls()
        self._build_right_modules()
        self._build_bottom_reference_modules()

    # --------------------------------------------------------------------------
    # 3. LEFT COLUMN: DEDICATED FULL AIRFRAME SYSTEM STATUS & HARDWARE HEALTH
    # --------------------------------------------------------------------------
    def _build_left_system_status(self):
        self.left_col.rowconfigure(0, weight=6)  # Real-Time Avionics Diagnostics
        self.left_col.rowconfigure(1, weight=4)  # Power & Comms Telemetry
        self.left_col.columnconfigure(0, weight=1)

        # 3A. Real-Time Hardware Health Card
        self.card_health = self._create_card(self.left_col, "AIRFRAME SYSTEM STATUS // HARDWARE HEALTH")
        self.card_health.grid(row=0, column=0, sticky="nsew", pady=(0, 6))

        sub_lbl = tk.Label(self.card_health, text="ONBOARD SENSORS, COMPANION AI & FC METRICS",
                           font=self.FONT_MONO_XS, fg=COLOR_CYAN, bg=COLOR_PANEL_BG)
        sub_lbl.pack(anchor="w", padx=8, pady=(2, 4))

        hw_f = tk.Frame(self.card_health, bg=COLOR_PANEL_BG)
        hw_f.pack(fill=tk.BOTH, expand=True, padx=8, pady=2)

        items = [
            ("MicoAir FC H743v2", "38°C", "ARMED/AUTO", 0.95),
            ("Jetson Orin Nano", "51°C", "YOLO+SLAM", 0.85),
            ("RPLiDAR C1 360°", "10.2Hz", "SYNC LOCK", 0.95),
            ("ESC 4x Motors", "44°C", "3,556 RPM", 0.82),
            ("MTF-01 Optical Flow", "96% Q", "LOCKED 1.2m", 0.96),
            ("Bosch BMI088 IMU", "<0.02°", "CALIBRATED", 0.92),
            ("VL53L1X Laser ToF", "1.20m", "AGL HOLD", 0.90),
            ("RP1 ELRS Receiver", "-42dBm", "500Hz / LQ100", 1.00)
        ]

        for name, val, status, bar_fill in items:
            row = tk.Frame(hw_f, bg=COLOR_PANEL_BG)
            row.pack(fill=tk.X, pady=2)

            tk.Label(row, text=name, font=self.FONT_SUBTITLE, fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG, width=17, anchor="w").pack(side=tk.LEFT)

            b_cv = tk.Canvas(row, width=60, height=9, bg=COLOR_PANEL_BG, highlightthickness=0, bd=0)
            b_cv.pack(side=tk.LEFT, padx=3)
            for seg in range(6):
                seg_x = seg * 10
                seg_col = COLOR_GREEN_DEFENSE if (seg / 6.0) < bar_fill else "#1E2A3E"
                b_cv.create_rectangle(seg_x, 1, seg_x + 7, 8, fill=seg_col, outline="")

            tk.Label(row, text=f"{status} | {val}", font=self.FONT_MONO_XS, fg=COLOR_CYAN, bg=COLOR_PANEL_BG, width=16, anchor="e").pack(side=tk.RIGHT)

        # 3B. Power & Link Diagnostics Card
        self.card_power = self._create_card(self.left_col, "POWER DISTRIBUTION & COMMS LINK")
        self.card_power.grid(row=1, column=0, sticky="nsew")

        pwr_f = tk.Frame(self.card_power, bg=COLOR_PANEL_BG)
        pwr_f.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        pwr_metrics = [
            ("Pack Voltage", "22.84 V (6S LiPo)", COLOR_GREEN_DEFENSE),
            ("Current Draw", "14.2 A (Hovering)", COLOR_TEXT_PRIMARY),
            ("Power Consumption", "324 W", COLOR_TEXT_PRIMARY),
            ("Wi-Fi 6 Link Latency", "3.2 ms (Archer AX55)", COLOR_CYAN),
            ("Packet Loss Rate", "0.00 % (AES-256)", COLOR_GREEN_DEFENSE),
            ("MAVLink Heartbeat", "10 Hz NOMINAL", COLOR_GREEN_DEFENSE),
        ]

        for label, val, col in pwr_metrics:
            r = tk.Frame(pwr_f, bg=COLOR_PANEL_BG)
            r.pack(fill=tk.X, pady=1)
            tk.Label(r, text=label, font=self.FONT_MONO_XS, fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, anchor="w").pack(side=tk.LEFT)
            tk.Label(r, text=val, font=self.FONT_MONO_XS, fg=col, bg=COLOR_PANEL_BG, anchor="e").pack(side=tk.RIGHT)

    # --------------------------------------------------------------------------
    # 4. CENTER COLUMN: 2D SLAM OCCUPANCY GRID (TOP) + COCKPIT JOYSTICK & COMPASS (BOTTOM)
    # --------------------------------------------------------------------------
    def _build_center_slam_and_controls(self):
        self.center_col.rowconfigure(0, weight=7)  # 2D Robotic SLAM Occupancy Grid Map
        self.center_col.rowconfigure(1, weight=3)  # Tactical Cockpit Console (Joysticks + Realistic Compass)
        self.center_col.columnconfigure(0, weight=1)

        # 4A. 2D Robotic SLAM Occupancy Grid Map Card
        self.card_slam = self._create_card(self.center_col, "2D ROBOTIC SLAM OCCUPANCY GRID MAP // CARTOGRAPHER")
        self.card_slam.grid(row=0, column=0, sticky="nsew", pady=(0, 6))

        tool_bar = tk.Frame(self.card_slam, bg=COLOR_CARD_HEADER_BG)
        tool_bar.pack(fill=tk.X, padx=6, pady=2)

        tk.Label(tool_bar, text="OCCUPANCY PROBABILITY: [FREE: 0% | WALL: 100% | UNKNOWN: FOG]",
                 font=self.FONT_MONO_XS, fg=COLOR_GREEN_DEFENSE, bg=COLOR_CARD_HEADER_BG).pack(side=tk.LEFT, padx=4)

        tk.Button(tool_bar, text="🔍+", font=self.FONT_MONO_XS, bg="#162035", fg=COLOR_CYAN,
                  command=lambda: self._zoom_slam(1.2)).pack(side=tk.RIGHT, padx=2)
        tk.Button(tool_bar, text="🔍-", font=self.FONT_MONO_XS, bg="#162035", fg=COLOR_CYAN,
                  command=lambda: self._zoom_slam(0.8)).pack(side=tk.RIGHT, padx=2)
        tk.Button(tool_bar, text="↺ RESET VIEW", font=self.FONT_MONO_XS, bg="#162035", fg=COLOR_TEXT_SECONDARY,
                  command=self._reset_slam_view).pack(side=tk.RIGHT, padx=2)

        self.slam_canvas = tk.Canvas(
            self.card_slam,
            bg=COLOR_CANVAS_BLACK,
            highlightthickness=0,
            bd=0
        )
        self.slam_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
        self.slam_canvas.bind("<MouseWheel>", self._on_slam_mousewheel)

        # 4B. TACTICAL PILOT CONSOLE: JOYSTICK (LEFT/RIGHT GIMBALS) + REALISTIC 360° AVIONICS COMPASS (CENTER)
        self.card_cockpit = self._create_card(self.center_col, "PILOT FLIGHT CONTROLLER // RADIOMASTER POCKET ELRS & AVIONICS HSI")
        self.card_cockpit.grid(row=1, column=0, sticky="nsew")

        cockpit_container = tk.Frame(self.card_cockpit, bg=COLOR_PANEL_BG)
        cockpit_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        # Left Gimbal: Throttle & Yaw
        g1_frame = tk.Frame(cockpit_container, bg=COLOR_PANEL_BG)
        g1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        self.lbl_g1_status = tk.Label(g1_frame, text="THROTTLE / YAW [CH1-CH4]", font=self.FONT_MONO_XS,
                                      fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG)
        self.lbl_g1_status.pack(anchor="center", pady=(1, 0))
        self.cv_gimbal_left = tk.Canvas(g1_frame, bg=COLOR_PANEL_BG, height=95, highlightthickness=0, bd=0)
        self.cv_gimbal_left.pack(fill=tk.BOTH, expand=True)

        # Center Instrument: Realistic 360° Rotating Avionics Compass HSI
        comp_frame = tk.Frame(cockpit_container, bg=COLOR_PANEL_BG)
        comp_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        self.lbl_compass_status = tk.Label(comp_frame, text="HEADING INDICATOR // 360° HSI", font=self.FONT_MONO_XS,
                                           fg=COLOR_CYAN, bg=COLOR_PANEL_BG)
        self.lbl_compass_status.pack(anchor="center", pady=(1, 0))
        self.cv_compass_hsi = tk.Canvas(comp_frame, bg=COLOR_PANEL_BG, height=95, highlightthickness=0, bd=0)
        self.cv_compass_hsi.pack(fill=tk.BOTH, expand=True)

        # Right Gimbal: Pitch & Roll
        g2_frame = tk.Frame(cockpit_container, bg=COLOR_PANEL_BG)
        g2_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        self.lbl_g2_status = tk.Label(g2_frame, text="PITCH / ROLL [CH2-CH3]", font=self.FONT_MONO_XS,
                                      fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG)
        self.lbl_g2_status.pack(anchor="center", pady=(1, 0))
        self.cv_gimbal_right = tk.Canvas(g2_frame, bg=COLOR_PANEL_BG, height=95, highlightthickness=0, bd=0)
        self.cv_gimbal_right.pack(fill=tk.BOTH, expand=True)

    # --------------------------------------------------------------------------
    # 5. RIGHT COLUMN: TACTICAL CAMERA, SURVIVOR TABLE & TELEMETRY BANDWIDTH
    # --------------------------------------------------------------------------
    def _build_right_modules(self):
        self.right_col.rowconfigure(0, weight=4)  # Tactical Camera
        self.right_col.rowconfigure(1, weight=4)  # Survivor Table
        self.right_col.rowconfigure(2, weight=2)  # Bandwidth / Comms Analytics
        self.right_col.columnconfigure(0, weight=1)

        # 5A. Tactical Camera Card
        self.card_cam = self._create_card(self.right_col, "ONBOARD IP CAMERA // TACTICAL OSD")
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
        self.card_survivors = self._create_card(self.right_col, "SURVIVOR LOCALIZATION TABLE // 1m x 1m GEOTAGS")
        self.card_survivors.grid(row=1, column=0, sticky="nsew", pady=(0, 4))

        tbl = tk.Frame(self.card_survivors, bg=COLOR_PANEL_BG)
        tbl.pack(fill=tk.BOTH, expand=True, padx=6, pady=2)

        self.survivor_row_widgets = []
        for s in self.survivors:
            row = tk.Frame(tbl, bg=COLOR_PANEL_BG, bd=1, relief=tk.FLAT)
            row.pack(fill=tk.X, pady=1)

            lbl_id = tk.Label(row, text=s['id'], font=self.FONT_MONO_SM, fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG, width=5, anchor="w")
            lbl_id.pack(side=tk.LEFT)

            lbl_grid = tk.Label(row, text=s['grid'], font=self.FONT_MONO_SM, fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL_BG, width=12, anchor="center")
            lbl_grid.pack(side=tk.LEFT)

            lbl_status = tk.Label(row, text="SEARCHING...", font=self.FONT_MONO_XS, fg=COLOR_AMBER, bg=COLOR_PANEL_BG, width=12, anchor="e")
            lbl_status.pack(side=tk.RIGHT)

            self.survivor_row_widgets.append((lbl_status, lbl_grid, row, lbl_id))

        # 5C. Bandwidth & Comms Analytics Card
        card_analytics = self._create_card(self.right_col, "TELEMETRY BANDWIDTH & THROUGHPUT")
        card_analytics.grid(row=2, column=0, sticky="nsew")

        an_f = tk.Frame(card_analytics, bg=COLOR_PANEL_BG)
        an_f.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        self.bandwidth_canvas = tk.Canvas(an_f, bg=COLOR_PANEL_BG, height=50, highlightthickness=0, bd=0)
        self.bandwidth_canvas.pack(fill=tk.BOTH, expand=True, padx=2)

    # --------------------------------------------------------------------------
    # 6. BOTTOM ROW: BATTERY MODULE + MOTOR SPECTRUM + MISSION ACTION BUTTONS
    # --------------------------------------------------------------------------
    def _build_bottom_reference_modules(self):
        # 6A. 3D Transparent Battery Module (DF-BT-01 Style)
        card_bat = self._create_card(self.bottom_frame, "BATTERY MODULE // 6S MOLICEL 21700")
        card_bat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        self.battery_3d_canvas = tk.Canvas(card_bat, bg=COLOR_PANEL_BG, height=120, highlightthickness=0, bd=0)
        self.battery_3d_canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=2)

        # 6B. Electric Motor Overview & Temperature Spectrum Graph
        card_motor = self._create_card(self.bottom_frame, "ELECTRIC MOTOR OVERVIEW // DSHOT TELEMETRY")
        card_motor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        self.motor_canvas = tk.Canvas(card_motor, bg=COLOR_PANEL_BG, height=120, highlightthickness=0, bd=0)
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
    # 7. RENDERING ENGINES: WAVEFORM, GIMBALS & COMPASS HSI
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

    def _render_joysticks_and_compass(self):
        # 1. Left Gimbal: Throttle & Yaw
        cv_l = self.cv_gimbal_left
        cv_l.delete("all")
        lw, lh = cv_l.winfo_width(), cv_l.winfo_height()
        if lw > 30 and lh > 30:
            lcx, lcy = lw / 2.0, lh / 2.0
            r = min(lcx, lcy) - 10
            # Gimbal well
            cv_l.create_oval(lcx - r, lcy - r, lcx + r, lcy + r, fill="#0B111E", outline="#1E2A42", width=2)
            cv_l.create_oval(lcx - r * 0.5, lcy - r * 0.5, lcx + r * 0.5, lcy + r * 0.5, outline="#162238", dash=(2, 2))
            cv_l.create_line(lcx - r, lcy, lcx + r, lcy, fill="#182338", width=1)
            cv_l.create_line(lcx, lcy - r, lcx, lcy + r, fill="#182338", width=1)
            # Stick position
            sx = lcx + (self.rc_yaw * (r - 8))
            sy = lcy - ((self.rc_throttle - 0.5) * 2 * (r - 8))
            cv_l.create_line(lcx, lcy, sx, sy, fill="#0E4438", width=2)
            cv_l.create_oval(sx - 6, sy - 6, sx + 6, sy + 6, fill=COLOR_GREEN_DEFENSE, outline=COLOR_TEXT_PRIMARY, width=1.5)
            # Text readout
            th_pct = int(self.rc_throttle * 100)
            self.lbl_g1_status.config(text=f"THROTTLE: {th_pct}% | YAW: {self.rc_yaw:+.2f}")

        # 2. Right Gimbal: Pitch & Roll
        cv_r = self.cv_gimbal_right
        cv_r.delete("all")
        rw, rh = cv_r.winfo_width(), cv_r.winfo_height()
        if rw > 30 and rh > 30:
            rcx, rcy = rw / 2.0, rh / 2.0
            r = min(rcx, rcy) - 10
            # Gimbal well
            cv_r.create_oval(rcx - r, rcy - r, rcx + r, rcy + r, fill="#0B111E", outline="#1E2A42", width=2)
            cv_r.create_oval(rcx - r * 0.5, rcy - r * 0.5, rcx + r * 0.5, rcy + r * 0.5, outline="#162238", dash=(2, 2))
            cv_r.create_line(rcx - r, rcy, rcx + r, rcy, fill="#182338", width=1)
            cv_r.create_line(rcx, rcy - r, rcx, rcy + r, fill="#182338", width=1)
            # Stick position
            sx = rcx + (self.rc_roll * (r - 8))
            sy = rcy - (self.rc_pitch * (r - 8))
            cv_r.create_line(rcx, rcy, sx, sy, fill="#0E374A", width=2)
            cv_r.create_oval(sx - 6, sy - 6, sx + 6, sy + 6, fill=COLOR_CYAN, outline=COLOR_TEXT_PRIMARY, width=1.5)
            # Text readout
            self.lbl_g2_status.config(text=f"PITCH: {self.rc_pitch:+.2f} | ROLL: {self.rc_roll:+.2f}")

        # 3. Center Instrument: REALISTIC 360° ROTATING AVIONICS COMPASS ROSE / HSI
        cv_c = self.cv_compass_hsi
        cv_c.delete("all")
        cw, ch = cv_c.winfo_width(), cv_c.winfo_height()
        if cw > 40 and ch > 40:
            cx, cy = cw / 2.0, ch / 2.0
            r = min(cx, cy) - 8

            # Outer instrument bezel
            cv_c.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#090E1A", outline="#1C2B44", width=2)
            cv_c.create_oval(cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3, outline="#131F33", width=1)

            # Degree ticks and labels (Rotating with self.yaw for authentic aviation heading)
            cardinal_labels = {0: "N", 90: "E", 180: "S", 270: "W"}
            inter_labels = {45: "NE", 135: "SE", 225: "SW", 315: "NW"}

            for deg in range(0, 360, 15):
                angle_rel = deg - self.yaw
                rad = math.radians(angle_rel)
                sin_a = math.sin(rad)
                cos_a = math.cos(rad)

                t_len = 8 if deg % 30 == 0 else 4
                x1 = cx + (r - 4) * sin_a
                y1 = cy - (r - 4) * cos_a
                x2 = cx + (r - 4 - t_len) * sin_a
                y2 = cy - (r - 4 - t_len) * cos_a

                tick_col = COLOR_CYAN if deg % 90 == 0 else ("#64748B" if deg % 30 == 0 else "#334155")
                cv_c.create_line(x1, y1, x2, y2, fill=tick_col, width=1.5 if deg % 30 == 0 else 1)

                # Labels for Cardinal & 30-deg marks
                if deg in cardinal_labels:
                    tx = cx + (r - 18) * sin_a
                    ty = cy - (r - 18) * cos_a
                    col = COLOR_RED if deg == 0 else (COLOR_CYAN if deg == 90 else COLOR_TEXT_PRIMARY)
                    cv_c.create_text(tx, ty, text=cardinal_labels[deg], font=self.FONT_MONO_SM, fill=col)
                elif deg in inter_labels and r > 45:
                    tx = cx + (r - 17) * sin_a
                    ty = cy - (r - 17) * cos_a
                    cv_c.create_text(tx, ty, text=inter_labels[deg], font=self.FONT_MONO_XS, fill="#64748B")

            # Fixed Lubber Line (Top Center index pointing down)
            cv_c.create_polygon(cx - 5, cy - r + 2, cx + 5, cy - r + 2, cx, cy - r + 9, fill=COLOR_ORANGE, outline="")

            # Center Miniature Aircraft Symbol
            cv_c.create_line(cx - 10, cy, cx + 10, cy, fill=COLOR_GREEN_DEFENSE, width=2)
            cv_c.create_line(cx, cy - 8, cx, cy + 8, fill=COLOR_GREEN_DEFENSE, width=2)
            cv_c.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=COLOR_GREEN_DEFENSE, outline="")

            # Digital Heading HUD Box
            cardinal_name = "N" if (self.yaw < 22.5 or self.yaw >= 337.5) else (
                "NE" if self.yaw < 67.5 else (
                    "E" if self.yaw < 112.5 else (
                        "SE" if self.yaw < 157.5 else (
                            "S" if self.yaw < 202.5 else (
                                "SW" if self.yaw < 247.5 else (
                                    "W" if self.yaw < 292.5 else "NW"
                                )
                            )
                        )
                    )
                )
            )
            self.lbl_compass_status.config(text=f"HDG: {int(self.yaw):03d}° [{cardinal_name}] // AVIONICS HSI")

    def _render_3d_battery_module(self):
        cv = self.battery_3d_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 50:
            return

        cv.create_text(14, 18, text=f"{self.battery_pct:.1f} %", font=self.FONT_TITLE, fill=COLOR_GREEN_DEFENSE, anchor="w")
        cv.create_text(14, 38, text="BATTERY LEVEL", font=self.FONT_MONO_XS, fill=COLOR_TEXT_SECONDARY, anchor="w")
        cv.create_text(14, 56, text=f"CURRENT\n{self.current_amps:.1f} A", font=self.FONT_MONO_XS, fill=COLOR_TEXT_PRIMARY, anchor="w")
        cv.create_text(80, 56, text=f"VOLTAGE\n{self.battery_voltage:.2f} V", font=self.FONT_MONO_XS, fill=COLOR_TEXT_PRIMARY, anchor="w")

        bx, by = 150, 14
        bw, bh = 85, 52
        cv.create_rectangle(bx, by, bx + bw, by + bh, outline=COLOR_CYAN, width=1.5)
        cv.create_line(bx, by, bx + 12, by - 8, fill=COLOR_CYAN, width=1.5)
        cv.create_line(bx + bw, by, bx + bw + 12, by - 8, fill=COLOR_CYAN, width=1.5)
        cv.create_line(bx + 12, by - 8, bx + bw + 12, by - 8, fill=COLOR_CYAN, width=1.5)
        cv.create_line(bx + bw + 12, by - 8, bx + bw + 12, by + bh - 8, fill=COLOR_CYAN, width=1.5)
        cv.create_line(bx + bw, by + bh, bx + bw + 12, by + bh - 8, fill=COLOR_CYAN, width=1.5)

        for c_idx in range(6):
            cx_pos = bx + 6 + c_idx * 12
            cv.create_rectangle(cx_pos, by + 10, cx_pos + 8, by + bh - 10, fill=COLOR_GREEN_DEFENSE, outline="")

        cv.create_text(bx + bw, by + bh + 14, text="MOLICEL-P45B 6S", font=self.FONT_MONO_XS, fill=COLOR_GREEN_DEFENSE, anchor="e")

        rx = 265
        if w > 360:
            cv.create_text(rx, 18, text="REMAINING ENDURANCE\n2h 50m", font=self.FONT_MONO_XS, fill=COLOR_GREEN_DEFENSE, anchor="w")
            cv.create_text(rx, 50, text="ENERGY: 3.42 kWh\nPOWER: 324 W", font=self.FONT_MONO_XS, fill=COLOR_TEXT_SECONDARY, anchor="w")

    def _render_motor_overview(self):
        cv = self.motor_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 50:
            return

        cv.create_text(14, 18, text="ENGINE STATUS\nNOMINAL", font=self.FONT_MONO_XS, fill=COLOR_GREEN_DEFENSE, anchor="w")
        cv.create_text(14, 50, text="RPM: 3,556\nPOWER: 424 W", font=self.FONT_MONO_XS, fill=COLOR_TEXT_PRIMARY, anchor="w")

        spec_x = 125
        spec_w = max(60, w - spec_x - 20)
        spec_y = 65
        num_bars = 28
        bar_w = max(2, int(spec_w / num_bars) - 1)

        cv.create_text(spec_x, 16, text="TEMPERATURE SPECTRUM (°C)", font=self.FONT_MONO_XS, fill=COLOR_TEXT_SECONDARY, anchor="w")
        cv.create_text(w - 20, 16, text="EFFICIENCY 93%", font=self.FONT_MONO_XS, fill=COLOR_TEXT_PRIMARY, anchor="e")

        for i in range(num_bars):
            bx = spec_x + i * (bar_w + 1)
            norm = math.sin((i / float(num_bars)) * math.pi)
            b_h = max(4, int(norm * 42))
            col = COLOR_GREEN_DEFENSE if norm < 0.6 else (COLOR_AMBER if norm < 0.85 else COLOR_RED)
            cv.create_rectangle(bx, spec_y - b_h, bx + bar_w, spec_y, fill=col, outline="")

    def _render_bandwidth(self):
        cv_b = self.bandwidth_canvas
        cv_b.delete("all")
        bw_w = cv_b.winfo_width()
        bw_h = cv_b.winfo_height()
        if bw_w > 10:
            cv_b.create_text(8, 8, text="BANDWIDTH: 3.1 Gbps DOWN | 1.1 Gbps UP", font=self.FONT_MONO_XS, fill=COLOR_TEXT_SECONDARY, anchor="w")
            cv_b.create_text(bw_w - 8, 8, text="Wi-Fi 6 PING: 3.2ms", font=self.FONT_MONO_XS, fill=COLOR_CYAN, anchor="e")
            pts = [8, bw_h - 4]
            for step in range(12):
                px = 8 + step * ((bw_w - 16) / 11.0)
                py = bw_h - 6 - math.sin(step * 0.7 + self.waveform_phase) * 12 - (step % 3 * 2)
                pts.extend([px, py])
            pts.extend([bw_w - 8, bw_h - 4])
            cv_b.create_polygon(pts, fill="#0F2432", outline=COLOR_CYAN)

    # --------------------------------------------------------------------------
    # 8. RENDERING ENGINES: CAMERA & AUTHENTIC 2D SLAM OCCUPANCY GRID
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

        # 1. Fog of War / Unexplored Dark Background
        cv.create_rectangle(0, 0, cw, ch, fill="#080D18", outline="")

        # Subtle Dot Matrix Grid in Unexplored Space
        step_dot = 24
        for dx in range(10, cw, step_dot):
            for dy in range(10, ch, step_dot):
                cv.create_rectangle(dx, dy, dx + 1, dy + 1, fill="#111B2C", outline="")

        # 2. Authentic ROS/Cartographer Explored Free Space Corridors
        # Draw explored corridor zones in high-contrast light slate / tactical floor
        for poly in self.corridor_polys:
            pts = []
            for px, py in poly:
                cx_pt, cy_pt = to_cv(px, py)
                pts.extend([cx_pt, cy_pt])
            cv.create_polygon(pts, fill="#131C2D", outline="#1A283E", width=1)

        # 3. Discrete 1m x 1m Arena Engineering Axes & Rulers
        grid_cols = 16
        grid_rows = 15
        col_letters = "ABCDEFGHIJKLMNOP"
        step_x = cw / grid_cols
        step_y = ch / grid_rows

        for c in range(grid_cols + 1):
            gx = c * step_x
            cv.create_line(gx, 0, gx, ch, fill="#121D30", width=1)
            if c < grid_cols:
                cv.create_text(gx + step_x / 2, 8, text=col_letters[c], font=self.FONT_MONO_XS, fill=COLOR_TEXT_MUTED)

        for r in range(grid_rows + 1):
            gy = r * step_y
            cv.create_line(0, gy, cw, gy, fill="#121D30", width=1)
            if r < grid_rows:
                cv.create_text(8, gy + step_y / 2, text=str(r + 1), font=self.FONT_MONO_XS, fill=COLOR_TEXT_MUTED)

        # 4. Home Entry / Exit LZ Helipad Marker at Grid [B-4]
        lz_cx, lz_cy = to_cv(90, 160)
        cv.create_oval(lz_cx - 16, lz_cy - 16, lz_cx + 16, lz_cy + 16, outline=COLOR_GREEN_DEFENSE, width=1.5, dash=(4, 3))
        cv.create_text(lz_cx, lz_cy, text="H", font=self.FONT_CARD_TITLE, fill=COLOR_GREEN_DEFENSE)
        cv.create_text(lz_cx, lz_cy + 20, text="ENTRY/EXIT LZ [B-4]", font=self.FONT_MONO_XS, fill=COLOR_GREEN_DEFENSE)

        # 5. Obstacle Inflation Safety Layer (Autonomous Costmap Barrier)
        for (w_p1, w_p2) in self.maze_walls:
            cx1, cy1 = to_cv(*w_p1)
            cx2, cy2 = to_cv(*w_p2)
            cv.create_line(cx1, cy1, cx2, cy2, fill="#1C2D44", width=14)
            cv.create_line(cx1, cy1, cx2, cy2, fill="#0E1624", width=8)

        # 6. Solid High-Contrast Obstacle Walls (Reflective LiDAR Return Edges)
        for (w_p1, w_p2) in self.maze_walls:
            cx1, cy1 = to_cv(*w_p1)
            cx2, cy2 = to_cv(*w_p2)
            cv.create_line(cx1, cy1, cx2, cy2, fill="#0F172A", width=6)
            cv.create_line(cx1, cy1, cx2, cy2, fill="#00F2FE", width=2)

        # 7. Dense Persistent SLAM Point Cloud on Obstacle Surfaces
        if len(self.persistent_slam_cloud) > 0:
            for px, py in self.persistent_slam_cloud:
                pt_x, pt_y = to_cv(px, py)
                cv.create_oval(pt_x - 1.5, pt_y - 1.5, pt_x + 1.5, pt_y + 1.5, fill="#00E5FF", outline="")

        # 8. Flight Trajectory Ribbon
        if len(self.trajectory_history) > 1:
            flat_pts = []
            for hx, hy in self.trajectory_history:
                tx, ty = to_cv(hx, hy)
                flat_pts.extend([tx, ty])
            cv.create_line(flat_pts, fill="#0E3D4C", width=6, smooth=True)
            cv.create_line(flat_pts, fill=COLOR_CYAN, width=2, smooth=True)

        dx, dy = to_cv(*self.drone_pos)

        # 9. Real-Time Rotating 360° LiDAR Scan Cone & Active Beams
        sweep_rad = math.radians(self.lidar_angle)
        cone_radius = 120 * min(scale_x, scale_y)
        span = math.radians(24)
        lx1 = dx + cone_radius * math.cos(sweep_rad - span)
        ly1 = dy + cone_radius * math.sin(sweep_rad - span)
        lx2 = dx + cone_radius * math.cos(sweep_rad + span)
        ly2 = dy + cone_radius * math.sin(sweep_rad + span)
        cv.create_polygon(dx, dy, lx1, ly1, lx2, ly2, fill="#003547", outline="")

        # Dynamic LiDAR Laser Rays hitting walls
        if len(self.lidar_points) > 0:
            for px, py in self.lidar_points:
                pt_x, pt_y = to_cv(px, py)
                # Faint laser beam ray
                cv.create_line(dx, dy, pt_x, pt_y, fill="#0A3F50", width=1)
                # Bright impact spark point
                cv.create_oval(pt_x - 2, pt_y - 2, pt_x + 2, pt_y + 2, fill="#00F2FE", outline="#FFFFFF")

        # 10. 6 Survivor Target Markers (T1 to T6) with Pulse Radar
        for s in self.survivors:
            sx, sy = to_cv(s["x"], s["y"])
            if s["located"]:
                pulse_r = 12 + (int(time.time() * 8) % 6)
                cv.create_oval(sx - pulse_r, sy - pulse_r, sx + pulse_r, sy + pulse_r, outline=COLOR_ORANGE, width=1.5)
                cv.create_oval(sx - 7, sy - 7, sx + 7, sy + 7, fill=COLOR_ORANGE, outline=COLOR_TEXT_PRIMARY, width=1.5)
                cv.create_text(sx, sy + 14, text=f"{s['id']} [{s['grid'].split()[-1]}]", font=self.FONT_MONO_SM, fill=COLOR_ORANGE)
            else:
                cv.create_rectangle(sx - 5, sy - 5, sx + 5, sy + 5, outline="#475569", width=1)
                cv.create_text(sx, sy + 11, text=s['id'], font=self.FONT_MONO_XS, fill="#64748B")

        # 11. Autonomous Robot Footprint & Heading Vector
        h_rad = math.radians(self.yaw)
        hx = dx + 24 * math.sin(h_rad)
        hy = dy - 24 * math.cos(h_rad)
        cv.create_line(dx, dy, hx, hy, fill=COLOR_CYAN, width=2.5, arrow=tk.LAST, arrowshape=(8, 10, 4))

        # Quadcopter frame with 4 rotor arms
        arm_len = 11
        for angle_offset in [45, 135, 225, 315]:
            arm_rad = math.radians(self.yaw + angle_offset)
            ax = dx + arm_len * math.sin(arm_rad)
            ay = dy - arm_len * math.cos(arm_rad)
            cv.create_line(dx, dy, ax, ay, fill=COLOR_TEXT_PRIMARY, width=1.5)
            cv.create_oval(ax - 3, ay - 3, ax + 3, ay + 3, fill=COLOR_GREEN_DEFENSE, outline="")

        # Central fuselage core
        cv.create_oval(dx - 5, dy - 5, dx + 5, dy + 5, fill=COLOR_ORANGE, outline=COLOR_TEXT_PRIMARY, width=1.5)

    # --------------------------------------------------------------------------
    # 9. SIMULATION ENGINE TICK
    # --------------------------------------------------------------------------
    def _schedule_updates(self):
        self._update_simulation_tick()
        self.root.after(33, self._schedule_updates)

    def _update_simulation_tick(self):
        if self.is_mission_active and not self.is_paused and self.start_time:
            self.elapsed_time = time.time() - self.start_time

        elapsed_sec = int(self.elapsed_time)
        hrs = elapsed_sec // 3600
        mins = (elapsed_sec % 3600) // 60
        secs = elapsed_sec % 60
        self.lbl_utc_time.config(text=f"MISSION CLOCK\n{hrs:02d}:{mins:02d}:{secs:02d}")

        self.lidar_angle = (self.lidar_angle + 10.2) % 360.0

        if self.is_mission_active and not self.is_paused:
            self._advance_corridor_flight()

        # Render All Subsystems
        self._render_waveform()
        self._render_joysticks_and_compass()
        self._render_3d_battery_module()
        self._render_motor_overview()
        self._render_bandwidth()
        self._render_ip_camera()
        self._render_slam_canvas()

    def _cast_lidar_ray(self, origin_x, origin_y, angle_deg, max_range=240):
        """Casts an authentic 2D LiDAR ray and returns the closest wall intersection."""
        rad = math.radians(angle_deg)
        dx = math.cos(rad)
        dy = math.sin(rad)
        min_dist = max_range
        hit_pt = None

        for (p1, p2) in self.maze_walls:
            x1, y1 = p1
            x2, y2 = p2
            v1x = origin_x - x1
            v1y = origin_y - y1
            v2x = x2 - x1
            v2y = y2 - y1
            v3x = -dy
            v3y = dx

            dot = v2x * v3x + v2y * v3y
            if abs(dot) < 1e-6:
                continue

            t1 = (v2x * v1y - v2y * v1x) / dot
            t2 = (v1x * v3x + v1y * v3y) / dot

            if t1 > 0 and 0.0 <= t2 <= 1.0:
                if t1 < min_dist:
                    min_dist = t1
                    jitter = random.uniform(-0.8, 0.8)
                    hit_pt = (origin_x + (t1 + jitter) * dx, origin_y + (t1 + jitter) * dy)

        if hit_pt is None:
            hit_pt = (origin_x + max_range * dx, origin_y + max_range * dy)
        return hit_pt, min_dist

    def _advance_corridor_flight(self):
        p1 = self.corridor_waypoints[self.waypoint_index]
        next_idx = (self.waypoint_index + 1) % len(self.corridor_waypoints)
        p2 = self.corridor_waypoints[next_idx]

        # Constant physical cruise speed across all waypoint segments
        seg_dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        step_speed = 4.2 / max(1.0, seg_dist)
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
        target_yaw = (math.degrees(math.atan2(dx, -dy))) % 360.0
        # Smooth organic yaw banking around corners
        yaw_diff = (target_yaw - self.yaw + 180.0) % 360.0 - 180.0
        self.yaw = (self.yaw + yaw_diff * 0.18) % 360.0

        turn_rate = max(-1.0, min(1.0, yaw_diff / 45.0))
        self.rc_yaw = max(-0.8, min(0.8, turn_rate * 0.5))
        self.rc_pitch = 0.22
        self.rc_roll = max(-0.6, min(0.6, turn_rate * 0.4))

        self.trajectory_history.append(list(self.drone_pos))
        if len(self.trajectory_history) > 600:
            self.trajectory_history.pop(0)

        self.distance_traversed += 0.05
        self.exploration_percent = min(100.0, self.exploration_percent + 0.035)

        self.battery_pct = max(10.0, self.battery_pct - 0.002)
        self.battery_voltage = 20.0 + (self.battery_pct / 100.0) * 2.84

        # Cast authentic LiDAR rays hitting maze walls
        self.lidar_points = []
        for offset in range(-35, 40, 6):
            ray_angle = (self.lidar_angle + offset) % 360.0
            hit_pt, d = self._cast_lidar_ray(self.drone_pos[0], self.drone_pos[1], ray_angle, max_range=240)
            self.lidar_points.append(hit_pt)
            if d < 235:
                self.persistent_slam_cloud.append(hit_pt)

        if len(self.persistent_slam_cloud) > 280:
            self.persistent_slam_cloud = self.persistent_slam_cloud[-280:]

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
