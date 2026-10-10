"""
================================================================================
TEAM EDITH - AIR MOUSE GROUND CONTROL STATION (GCS)
Autonomous GPS-Denied Indoor Search, Mapping & Survivor Localization Challenge
PS2: NIDAR AirMouse Challenge
================================================================================
"""

import tkinter as tk
from tkinter import ttk
import math
import time
import random
import threading

# Platform audio support
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


# ==============================================================================
# COLOR PALETTE & AESTHETIC CONFIGURATION (Dark Navy Blue Aerospace Theme)
# ==============================================================================
COLOR_BG_ROOT          = "#070B16"  # Deepest tactical space navy
COLOR_PANEL_BG         = "#0D1424"  # Dark navy container cards
COLOR_PANEL_BORDER     = "#1C2740"  # Structural card borders
COLOR_HEADER_BG        = "#0A1020"  # Top app bar background
COLOR_CARD_HEADER_BG   = "#131E35"  # Highlighted tab header bar background
COLOR_CANVAS_BLACK     = "#000000"  # Pure pitch black for SLAM canvas

# Accent Palette
COLOR_CYAN             = "#00F2FE"  # Primary laser & trajectory accent
COLOR_ORANGE           = "#FF6B00"  # Safety hazard orange (targets, warnings)
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
        if not HAS_WINSOUND:
            return
        def _beep():
            try:
                winsound.Beep(880, 80)
                winsound.Beep(1200, 120)
            except Exception:
                pass
        threading.Thread(target=_beep, daemon=True).start()

    @staticmethod
    def play_victory_alarm():
        """Distinct 3-tone victory chime on 6th target acquisition."""
        if not HAS_WINSOUND:
            return
        def _chime():
            try:
                winsound.Beep(988, 120)
                time.sleep(0.05)
                winsound.Beep(1175, 120)
                time.sleep(0.05)
                winsound.Beep(1568, 350)
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
        self.root.geometry("1480x880")
        self.root.minsize(1280, 760)
        self.root.configure(bg=COLOR_BG_ROOT)

        # Mission State
        self.is_mission_active = False
        self.is_simulation_mode = True
        self.start_time = None
        self.elapsed_time = 0.0

        # Drone State
        self.drone_armed = True
        self.altitude = 1.20
        self.pitch = 1.8
        self.roll = -0.4
        self.yaw = 198.0
        self.speed = 0.82
        self.distance_traversed = 0.0
        self.exploration_percent = 12.0

        # Arena Metric Grid: 15m x 15m
        self.grid_cols = [chr(c) for c in range(ord('A'), ord('P'))]  # A - O (15)
        self.grid_rows = list(range(1, 16))                          # 1 - 15

        # Survivors State (T1 - T6)
        self.survivors = [
            {"id": "T1", "status": "SEARCHING", "grid": "--", "conf": 0, "located": False},
            {"id": "T2", "status": "SEARCHING", "grid": "--", "conf": 0, "located": False},
            {"id": "T3", "status": "SEARCHING", "grid": "--", "conf": 0, "located": False},
            {"id": "T4", "status": "SEARCHING", "grid": "--", "conf": 0, "located": False},
            {"id": "T5", "status": "SEARCHING", "grid": "--", "conf": 0, "located": False},
            {"id": "T6", "status": "SEARCHING", "grid": "--", "conf": 0, "located": False},
        ]
        self.survivors_located_count = 0

        # Trajectory Waypoints & Point Cloud Accumulator
        self.drone_pos = [250, 80]     # Start at Home LZ (G-2 area)
        self.trajectory_history = [list(self.drone_pos)]
        self.point_cloud_dots = []     # (x, y, color)
        self.lidar_angle = 0.0

        # Pre-seed simulated indoor maze walls (LiDAR Point Cloud Scatter)
        self._init_maze_point_cloud()

        # Build Interface
        self._build_top_header()
        self._build_main_layout()
        self._build_bottom_bar()

        # Start periodic tick timers
        self._schedule_updates()

    # --------------------------------------------------------------------------
    # HELPER: TACTICAL HIGHLIGHTED CARD CONTAINER
    # --------------------------------------------------------------------------
    def _create_tactical_card(self, parent, title, accent_color=COLOR_CYAN, right_badge="···", width=None):
        """Creates a modern aerospace card container with a prominent highlighted header strip."""
        card = tk.Frame(parent, bg=COLOR_PANEL_BG, highlightthickness=1, highlightbackground=COLOR_PANEL_BORDER)
        if width:
            card.config(width=width)

        # Highlighted Header Bar
        hdr = tk.Frame(card, bg=COLOR_CARD_HEADER_BG, height=28)
        hdr.pack(side=tk.TOP, fill=tk.X)
        hdr.pack_propagate(False)

        # Left Neon Accent Bar
        accent_bar = tk.Frame(hdr, bg=accent_color, width=4)
        accent_bar.pack(side=tk.LEFT, fill=tk.Y)

        # Bold Highlighted Title
        title_lbl = tk.Label(hdr, text=f"  {title.upper()}", font=("Segoe UI", 8, "bold"),
                             fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_HEADER_BG)
        title_lbl.pack(side=tk.LEFT, padx=2)

        # Right-side Status Tag / Badge
        badge_lbl = tk.Label(hdr, text=f"{right_badge}  ", font=("Consolas", 8, "bold"),
                             fg=accent_color, bg=COLOR_CARD_HEADER_BG)
        badge_lbl.pack(side=tk.RIGHT, padx=4)

        # Thin Header Bottom Divider
        divider = tk.Frame(card, bg=COLOR_PANEL_BORDER, height=1)
        divider.pack(side=tk.TOP, fill=tk.X)

        # Body Container
        body = tk.Frame(card, bg=COLOR_PANEL_BG)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=4, pady=4)

        return card, body

    # --------------------------------------------------------------------------
    # SIMULATED POINT CLOUD MAZE SETUP
    # --------------------------------------------------------------------------
    def _init_maze_point_cloud(self):
        """Generates realistic laser-scanned wall boundaries using scattered point clusters."""
        random.seed(42)
        wall_lines = [
            ((30, 30), (520, 30)),
            ((520, 30), (520, 350)),
            ((520, 350), (30, 350)),
            ((30, 350), (30, 30)),
            ((30, 110), (220, 110)),
            ((270, 110), (430, 110)),
            ((150, 110), (150, 260)),
            ((150, 260), (350, 260)),
            ((350, 260), (350, 110)),
            ((230, 180), (350, 180)),
            ((430, 110), (430, 290)),
            ((350, 290), (480, 290)),
        ]
        for (x1, y1), (x2, y2) in wall_lines:
            length = math.hypot(x2 - x1, y2 - y1)
            steps = int(length / 2.5)
            for i in range(steps):
                t = i / max(1, steps)
                bx = x1 + t * (x2 - x1)
                by = y1 + t * (y2 - y1)
                for _ in range(3):
                    px = bx + random.uniform(-1.5, 1.5)
                    py = by + random.uniform(-1.5, 1.5)
                    color = random.choice(["#E2E8F0", "#94A3B8", "#00F2FE", "#CBD5E1"])
                    self.point_cloud_dots.append((px, py, color))

    # --------------------------------------------------------------------------
    # TOP HEADER BAR
    # --------------------------------------------------------------------------
    def _build_top_header(self):
        header = tk.Frame(self.root, bg=COLOR_HEADER_BG, height=54, highlightthickness=1, highlightbackground=COLOR_PANEL_BORDER)
        header.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(6, 4))
        header.pack_propagate(False)

        # Left: Branding
        logo_frame = tk.Frame(header, bg=COLOR_HEADER_BG)
        logo_frame.pack(side=tk.LEFT, padx=8)

        brand_lbl = tk.Label(logo_frame, text="TEAM EDITH", font=("Segoe UI", 12, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_HEADER_BG)
        brand_lbl.pack(side=tk.LEFT)
        sub_brand = tk.Label(logo_frame, text=" | AIR MOUSE GCS", font=("Segoe UI", 10), fg=COLOR_CYAN, bg=COLOR_HEADER_BG)
        sub_brand.pack(side=tk.LEFT)

        # Center-Left: Flight Telemetry Readouts
        self.header_telemetry = tk.Label(
            header,
            text="STATUS: ARMED  |  ALT: 1.20m  |  MISSION TIME: 00:00:00.0",
            font=("Consolas", 9, "bold"),
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_HEADER_BG
        )
        self.header_telemetry.pack(side=tk.LEFT, padx=25)

        # Center-Right: Mode Switcher Pill
        mode_btn = tk.Button(
            header,
            text="[ SIMULATION (ACTIVE) ]  /  [ LIVE HARDWARE ]",
            font=("Consolas", 8, "bold"),
            fg=COLOR_ORANGE,
            bg="#162035",
            activebackground="#1E2E4A",
            activeforeground=COLOR_CYAN,
            relief=tk.FLAT,
            padx=10,
            pady=3,
            command=self._toggle_mode
        )
        mode_btn.pack(side=tk.LEFT, padx=10)

        # Far Right: Battery & Signal Gauges
        comm_frame = tk.Frame(header, bg=COLOR_HEADER_BG)
        comm_frame.pack(side=tk.RIGHT, padx=12)

        # 6S Battery Widget
        batt_box = tk.Frame(comm_frame, bg="#131E34", padx=8, pady=2, highlightthickness=1, highlightbackground=COLOR_PANEL_BORDER)
        batt_box.pack(side=tk.RIGHT, padx=6)
        self.batt_lbl = tk.Label(batt_box, text="6S BATT: 22.8V | 88%", font=("Consolas", 8, "bold"), fg=COLOR_CYAN, bg="#131E34")
        self.batt_lbl.pack(anchor=tk.W)
        self.cell_lbl = tk.Label(batt_box, text="C1:3.80 C2:3.81 C3:3.80 C4:3.80 C5:3.81 C6:3.80", font=("Consolas", 7), fg=COLOR_GREEN, bg="#131E34")
        self.cell_lbl.pack(anchor=tk.W)

        # Cellular Signal 5-Bar Widget
        signal_box = tk.Frame(comm_frame, bg="#131E34", padx=8, pady=2, highlightthickness=1, highlightbackground=COLOR_PANEL_BORDER)
        signal_box.pack(side=tk.RIGHT, padx=6)
        self.signal_lbl = tk.Label(signal_box, text="SIGNAL: 99%  |||||", font=("Consolas", 8, "bold"), fg=COLOR_GREEN, bg="#131E34")
        self.signal_lbl.pack(anchor=tk.W)
        self.ping_lbl = tk.Label(signal_box, text="-42 dBm | ~3ms | Wi-Fi 6", font=("Consolas", 7), fg=COLOR_TEXT_SECONDARY, bg="#131E34")
        self.ping_lbl.pack(anchor=tk.W)

    def _toggle_mode(self):
        self.is_simulation_mode = not self.is_simulation_mode
        self._log_event(f"[MODE] Switched to {'SIMULATION' if self.is_simulation_mode else 'LIVE HARDWARE'}")

    # --------------------------------------------------------------------------
    # MAIN BODY LAYOUT (Left Column, Center SLAM, Right Column)
    # --------------------------------------------------------------------------
    def _build_main_layout(self):
        main_container = tk.Frame(self.root, bg=COLOR_BG_ROOT)
        main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=2)

        # ----------------------------------------------------------------------
        # COLUMN 1: Compass Gauge & 4-System Hardware Health (Highlighted Tabs)
        # ----------------------------------------------------------------------
        col1 = tk.Frame(main_container, bg=COLOR_BG_ROOT, width=240)
        col1.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        col1.pack_propagate(False)

        # 1. 360° HEADING COMPASS (Highlighted Header)
        card_compass, body_compass = self._create_tactical_card(
            col1, title="360° Heading Compass Gauge", accent_color=COLOR_CYAN, right_badge="IMU YAW"
        )
        card_compass.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        self.compass_canvas = tk.Canvas(body_compass, width=220, height=140, bg=COLOR_PANEL_BG, highlightthickness=0)
        self.compass_canvas.pack(pady=2)
        self._render_compass_dial()

        self.attitude_lbl = tk.Label(body_compass, text="Pitch: +1.8°  |  Roll: -0.4°  |  Yaw: 198°",
                                     font=("Consolas", 8), fg=COLOR_CYAN, bg=COLOR_PANEL_BG)
        self.attitude_lbl.pack(pady=(0, 4))

        # 2. 4-SYSTEM HARDWARE HEALTH MATRIX (Highlighted Header)
        card_diag, body_diag = self._create_tactical_card(
            col1, title="4-System Hardware Health Matrix", accent_color=COLOR_GREEN, right_badge="DIAGNOSTICS"
        )
        card_diag.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        health_items = [
            ("MicoAir FC (H743)", "38°C", "MAVLink OK"),
            ("Jetson Orin Nano", "51°C", "YOLO Active"),
            ("ESC Motors (4X)", "44°C", "DShot SYNC"),
            ("Raspberry Pi 4", "46°C", "Comms Link"),
        ]
        self.diag_labels = []
        for name, temp, status in health_items:
            row = tk.Frame(body_diag, bg=COLOR_PANEL_BG, pady=5)
            row.pack(fill=tk.X, padx=6)
            tk.Label(row, text=name, font=("Segoe UI", 8, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG).pack(anchor=tk.W)
            meta = tk.Label(row, text=f"Temp: {temp}  |  {status}", font=("Consolas", 8), fg=COLOR_GREEN, bg=COLOR_PANEL_BG)
            meta.pack(anchor=tk.W)
            self.diag_labels.append(meta)

        # ----------------------------------------------------------------------
        # COLUMN 2: 2D Robotic SLAM Canvas (Highlighted Header)
        # ----------------------------------------------------------------------
        card_slam, body_slam = self._create_tactical_card(
            main_container, title="2D Robotic SLAM Occupancy Grid Map", accent_color=COLOR_ORANGE, right_badge="RVIZ / 1m GRID"
        )
        card_slam.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        self.slam_canvas = tk.Canvas(body_slam, bg=COLOR_CANVAS_BLACK, highlightthickness=0)
        self.slam_canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.slam_canvas.bind("<Configure>", lambda e: self._render_slam_canvas())

        # ----------------------------------------------------------------------
        # COLUMN 3: Right Sidebar (IP Camera & Survivor Table - Highlighted Tabs)
        # ----------------------------------------------------------------------
        col3 = tk.Frame(main_container, bg=COLOR_BG_ROOT, width=380)
        col3.pack(side=tk.RIGHT, fill=tk.Y)
        col3.pack_propagate(False)

        # 1. IP CAMERA CARD (Highlighted Header)
        card_cam, body_cam = self._create_tactical_card(
            col3, title="IP Camera Live Feed (30 FPS)", accent_color=COLOR_RED, right_badge="1280x720 OSD"
        )
        card_cam.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        self.cam_canvas = tk.Canvas(body_cam, width=360, height=185, bg="#05070C", highlightthickness=0)
        self.cam_canvas.pack(padx=2, pady=2)
        self._render_camera_hud()

        # 2. SURVIVOR LOCALIZATION TABLE (Highlighted Header)
        card_surv, body_surv = self._create_tactical_card(
            col3, title="Survivor Localization Table", accent_color=COLOR_ORANGE, right_badge="6 TARGETS"
        )
        card_surv.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Table Header
        th = tk.Frame(body_surv, bg="#131C30", pady=3)
        th.pack(fill=tk.X, padx=2, pady=(2, 0))
        tk.Label(th, text="ID", width=4, font=("Consolas", 8, "bold"), fg=COLOR_CYAN, bg="#131C30").pack(side=tk.LEFT)
        tk.Label(th, text="STATUS", width=11, font=("Consolas", 8, "bold"), fg=COLOR_CYAN, bg="#131C30").pack(side=tk.LEFT)
        tk.Label(th, text="GRID COORD", width=12, font=("Consolas", 8, "bold"), fg=COLOR_CYAN, bg="#131C30").pack(side=tk.LEFT)
        tk.Label(th, text="CONF %", width=8, font=("Consolas", 8, "bold"), fg=COLOR_CYAN, bg="#131C30").pack(side=tk.LEFT)

        # Table Rows
        self.survivor_row_widgets = []
        for s in self.survivors:
            rf = tk.Frame(body_surv, bg=COLOR_PANEL_BG, pady=4)
            rf.pack(fill=tk.X, padx=2)
            lbl_id = tk.Label(rf, text=s["id"], width=4, font=("Consolas", 8, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL_BG)
            lbl_id.pack(side=tk.LEFT)
            lbl_st = tk.Label(rf, text="SEARCHING", width=11, font=("Consolas", 8), fg=COLOR_AMBER, bg=COLOR_PANEL_BG)
            lbl_st.pack(side=tk.LEFT)
            lbl_gd = tk.Label(rf, text="--", width=12, font=("Consolas", 8, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL_BG)
            lbl_gd.pack(side=tk.LEFT)
            lbl_cf = tk.Label(rf, text="0.0%", width=8, font=("Consolas", 8), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL_BG)
            lbl_cf.pack(side=tk.LEFT)
            self.survivor_row_widgets.append((lbl_st, lbl_gd, lbl_cf))

    # --------------------------------------------------------------------------
    # BOTTOM ACTION & LOGGING BAR (Highlighted Headers)
    # --------------------------------------------------------------------------
    def _build_bottom_bar(self):
        bottom = tk.Frame(self.root, bg=COLOR_BG_ROOT, height=140)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=(0, 6))
        bottom.pack_propagate(False)

        # 1. Mission Event Log Console (Highlighted Header)
        card_log, body_log = self._create_tactical_card(
            bottom, title="Mission Event Log", accent_color=COLOR_CYAN, right_badge="LIVE AUDIT"
        )
        card_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        self.log_text = tk.Text(body_log, bg="#050811", fg=COLOR_TEXT_SECONDARY, font=("Consolas", 8),
                                bd=0, highlightthickness=0, wrap=tk.NONE)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 2. Arena Exploration & Mission Progress Box (Highlighted Header)
        card_prog, body_prog = self._create_tactical_card(
            bottom, title="Arena Exploration & Mission Progress", accent_color=COLOR_CYAN, right_badge="ANALYTICS", width=360
        )
        card_prog.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        card_prog.pack_propagate(False)

        self.prog_bar_canvas = tk.Canvas(body_prog, width=340, height=22, bg="#070C18", highlightthickness=0)
        self.prog_bar_canvas.pack(padx=4, pady=(4, 2))

        self.prog_stats_lbl = tk.Label(
            body_prog,
            text="ARENA EXPLORED: 12%  |  DISTANCE: 0.0m\nPHASE: CORRIDOR MAPPING  |  TARGETS: 0 / 6 FOUND",
            font=("Consolas", 8, "bold"),
            fg=COLOR_CYAN,
            bg=COLOR_PANEL_BG,
            justify=tk.LEFT
        )
        self.prog_stats_lbl.pack(padx=4, pady=2, anchor=tk.W)

        # 3. Action Controls (Highlighted Header)
        card_ctrl, body_ctrl = self._create_tactical_card(
            bottom, title="Action Controls", accent_color=COLOR_ORANGE, right_badge="PILOT SAFETY", width=240
        )
        card_ctrl.pack(side=tk.RIGHT, fill=tk.Y)
        card_ctrl.pack_propagate(False)

        self.btn_start = tk.Button(
            body_ctrl,
            text="START MISSION",
            font=("Segoe UI", 9, "bold"),
            bg="#059669",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#10B981",
            relief=tk.FLAT,
            command=self._start_mission
        )
        self.btn_start.pack(fill=tk.X, padx=4, pady=(4, 2))

        self.btn_abort = tk.Button(
            body_ctrl,
            text="EMERGENCY ABORT (RTL)",
            font=("Segoe UI", 9, "bold"),
            bg="#DC2626",
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_RED,
            relief=tk.FLAT,
            command=self._emergency_abort
        )
        self.btn_abort.pack(fill=tk.X, padx=4, pady=2)

        # Seed initial log messages
        self._log_event("[BOOT] MicoAir H743v2 Stack Online (MAVLink v2.0)")
        self._log_event("[BOOT] RPLiDAR C1 Scanner Synchronized @ 10.2 Hz")
        self._log_event("[BOOT] Cartographer 2D Occupancy SLAM Pipeline Initialized")
        self._log_event("[READY] Entry LZ Geotagged at Grid [G-2]. Awaiting Launch.")

    # --------------------------------------------------------------------------
    # RENDERING METHODS (Compass, Camera HUD, SLAM Canvas)
    # --------------------------------------------------------------------------
    def _render_compass_dial(self):
        w, h = 220, 140
        cx, cy, r = w // 2, 65, 48
        self.compass_canvas.delete("all")

        self.compass_canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#1E2A44", width=2)
        self.compass_canvas.create_oval(cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8, outline="#141E34", width=1)

        cardinals = [("N", 0), ("E", 90), ("S", 180), ("W", 270)]
        for text, deg in cardinals:
            rad = math.radians(deg - self.yaw)
            tx = cx + (r - 14) * math.sin(rad)
            ty = cy - (r - 14) * math.cos(rad)
            col = COLOR_ORANGE if text == "N" else COLOR_TEXT_SECONDARY
            self.compass_canvas.create_text(tx, ty, text=text, font=("Consolas", 8, "bold"), fill=col)

        rad = math.radians(0)
        nx = cx + (r - 8) * math.sin(rad)
        ny = cy - (r - 8) * math.cos(rad)
        self.compass_canvas.create_line(cx, cy, nx, ny, fill=COLOR_ORANGE, width=3, arrow=tk.LAST)
        self.compass_canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=COLOR_TEXT_PRIMARY, outline="")

        self.compass_canvas.create_text(cx, cy + 52, text=f"{int(self.yaw)}° S", font=("Segoe UI", 11, "bold"), fill=COLOR_TEXT_PRIMARY)

    def _render_camera_hud(self):
        w, h = 360, 185
        self.cam_canvas.delete("all")

        self.cam_canvas.create_rectangle(0, 0, w, h, fill="#0F172A")
        self.cam_canvas.create_polygon(0, 0, 70, 45, 70, 140, 0, h, fill="#162035", outline="#1F2E4C")
        self.cam_canvas.create_polygon(w, 0, w - 70, 45, w - 70, 140, w, h, fill="#162035", outline="#1F2E4C")
        self.cam_canvas.create_rectangle(70, 45, w - 70, 140, fill="#0D1322", outline="#223254")

        self.cam_canvas.create_oval(14, 12, 22, 20, fill=COLOR_RED, outline="")
        self.cam_canvas.create_text(42, 16, text="REC", font=("Consolas", 8, "bold"), fill=COLOR_TEXT_PRIMARY)
        self.cam_canvas.create_text(w - 50, 16, text="30.0 FPS", font=("Consolas", 8), fill=COLOR_GREEN)

        for cx, cy in [(25, 30), (w - 25, 30), (25, h - 25), (w - 25, h - 25)]:
            self.cam_canvas.create_line(cx - 5, cy, cx + 5, cy, fill="#334155")
            self.cam_canvas.create_line(cx, cy - 5, cx, cy + 5, fill="#334155")

        if self.survivors_located_count > 0:
            bx1, by1, bx2, by2 = 145, 55, 215, 150
            self.cam_canvas.create_rectangle(bx1, by1, bx2, by2, outline=COLOR_ORANGE, width=2)
            self.cam_canvas.create_rectangle(bx1, by1 - 16, bx1 + 130, by1, fill=COLOR_ORANGE, outline="")
            self.cam_canvas.create_text(bx1 + 65, by1 - 8, text="SURVIVOR T1: 94.2%", font=("Consolas", 7, "bold"), fill=COLOR_TEXT_PRIMARY)

        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        self.cam_canvas.create_text(85, h - 12, text=ts, font=("Consolas", 7), fill=COLOR_TEXT_SECONDARY)
        self.cam_canvas.create_text(w - 70, h - 12, text="YOLOv8: ON", font=("Consolas", 7, "bold"), fill=COLOR_CYAN)

    def _render_slam_canvas(self):
        self.slam_canvas.delete("all")
        cw = self.slam_canvas.winfo_width()
        ch = self.slam_canvas.winfo_height()
        if cw < 50 or ch < 50:
            return

        cols_count = 15
        rows_count = 15
        gw = (cw - 50) / cols_count
        gh = (ch - 40) / rows_count

        for i, col_name in enumerate(self.grid_cols):
            x = 30 + i * gw
            self.slam_canvas.create_line(x, 20, x, ch - 20, fill="#0F182A", width=1)
            self.slam_canvas.create_text(x + gw / 2, ch - 10, text=col_name, font=("Consolas", 7), fill=COLOR_TEXT_MUTED)

        for j, row_idx in enumerate(self.grid_rows):
            y = 20 + j * gh
            self.slam_canvas.create_line(30, y, cw - 20, y, fill="#0F182A", width=1)
            self.slam_canvas.create_text(16, y + gh / 2, text=str(row_idx), font=("Consolas", 7), fill=COLOR_TEXT_MUTED)

        for px, py, pcol in self.point_cloud_dots:
            sx = 30 + (px / 550.0) * (cw - 60)
            sy = 20 + (py / 380.0) * (ch - 50)
            self.slam_canvas.create_rectangle(sx, sy, sx + 1.5, sy + 1.5, fill=pcol, outline="")

        dx = 30 + (self.drone_pos[0] / 550.0) * (cw - 60)
        dy = 20 + (self.drone_pos[1] / 380.0) * (ch - 50)
        cone_radius = 65
        sweep_rad = math.radians(self.lidar_angle)
        span = math.radians(45)
        x1 = dx + cone_radius * math.cos(sweep_rad - span)
        y1 = dy + cone_radius * math.sin(sweep_rad - span)
        x2 = dx + cone_radius * math.cos(sweep_rad + span)
        y2 = dy + cone_radius * math.sin(sweep_rad + span)
        self.slam_canvas.create_polygon(dx, dy, x1, y1, x2, y2, fill="#00354A", outline="")

        if len(self.trajectory_history) > 1:
            coords = []
            for hx, hy in self.trajectory_history:
                tx = 30 + (hx / 550.0) * (cw - 60)
                ty = 20 + (hy / 380.0) * (ch - 50)
                coords.extend([tx, ty])
            self.slam_canvas.create_line(coords, fill=COLOR_CYAN, width=2, smooth=True)

        lz_x = 30 + (250 / 550.0) * (cw - 60)
        lz_y = 20 + (80 / 380.0) * (ch - 50)
        self.slam_canvas.create_oval(lz_x - 6, lz_y - 6, lz_x + 6, lz_y + 6, fill=COLOR_GREEN, outline=COLOR_TEXT_PRIMARY, width=1)
        self.slam_canvas.create_text(lz_x + 36, lz_y - 10, text="Entry/Exit LZ", font=("Consolas", 7, "bold"), fill=COLOR_GREEN)

        if self.survivors[0]["located"]:
            t1_x = 30 + (100 / 550.0) * (cw - 60)
            t1_y = 20 + (180 / 380.0) * (ch - 50)
            self.slam_canvas.create_oval(t1_x - 7, t1_y - 7, t1_x + 7, t1_y + 7, fill=COLOR_ORANGE, outline=COLOR_TEXT_PRIMARY, width=2)
            self.slam_canvas.create_text(t1_x, t1_y - 12, text="T1 [C-4]", font=("Consolas", 7, "bold"), fill=COLOR_ORANGE)

        drone_r = 8
        self.slam_canvas.create_oval(dx - drone_r, dy - drone_r, dx + drone_r, dy + drone_r, fill=COLOR_ORANGE, outline=COLOR_TEXT_PRIMARY, width=1)
        self.slam_canvas.create_line(dx - drone_r - 4, dy, dx + drone_r + 4, dy, fill=COLOR_TEXT_PRIMARY, width=2)
        self.slam_canvas.create_line(dx, dy - drone_r - 4, dx, dy + drone_r + 4, fill=COLOR_TEXT_PRIMARY, width=2)

    # --------------------------------------------------------------------------
    # SIMULATION TICK & STATE UPDATES
    # --------------------------------------------------------------------------
    def _schedule_updates(self):
        self._update_telemetry_tick()
        self.root.after(50, self._schedule_updates)

    def _update_telemetry_tick(self):
        if self.is_mission_active and self.start_time:
            self.elapsed_time = time.time() - self.start_time
            m = int(self.elapsed_time // 60)
            s = int(self.elapsed_time % 60)
            ms = int((self.elapsed_time * 10) % 10)
            time_str = f"{m:02d}:{s:02d}.{ms:01d}"
            self.header_telemetry.config(text=f"STATUS: ARMED  |  ALT: {self.altitude:.2f}m  |  MISSION TIME: 00:{time_str}")

        self.lidar_angle = (self.lidar_angle + 6.0) % 360.0

        if self.is_mission_active:
            self._advance_simulation_flight()

        self._render_slam_canvas()
        self._render_compass_dial()
        self._render_progress_bar()

    def _advance_simulation_flight(self):
        speed = 1.2
        self.distance_traversed += 0.06
        self.exploration_percent = min(98.0, self.exploration_percent + 0.05)

        cx, cy = self.drone_pos
        if cy < 220 and cx > 80:
            self.drone_pos[0] -= speed * 0.8
            self.drone_pos[1] += speed * 0.5
            self.yaw = 225.0
        elif cx <= 80 and cy < 310:
            self.drone_pos[1] += speed
            self.yaw = 180.0
        elif cy >= 310 and cx < 400:
            self.drone_pos[0] += speed
            self.yaw = 90.0
        else:
            self.drone_pos[1] -= speed * 0.5
            self.yaw = 340.0

        self.trajectory_history.append(list(self.drone_pos))
        if len(self.trajectory_history) > 300:
            self.trajectory_history.pop(0)

        if self.elapsed_time >= 6.0 and not self.survivors[0]["located"]:
            self.survivors[0]["located"] = True
            self.survivors[0]["status"] = "LOCATED"
            self.survivors[0]["grid"] = "Grid [C-4]"
            self.survivors[0]["conf"] = 94.2
            self.survivors_located_count = 1

            lbl_st, lbl_gd, lbl_cf = self.survivor_row_widgets[0]
            lbl_st.config(text="LOCATED", fg=COLOR_ORANGE)
            lbl_gd.config(text="Grid [C-4]", fg=COLOR_ORANGE)
            lbl_cf.config(text="94.2%", fg=COLOR_GREEN)

            self._log_event("[ALERT] Survivor T1 Identified at Grid [C-4] (Temp: 37.1°C)")
            self._log_event("[SLAM] Discrete Geotag Registered: T1 -> Room Alpha [C-4]")
            AudioAlertSystem.play_sonar_chirp()

    def _render_progress_bar(self):
        pw = 340
        ph = 22
        self.prog_bar_canvas.delete("all")
        self.prog_bar_canvas.create_rectangle(0, 0, pw, ph, fill="#0F172A", outline="#1E2A42")
        fill_w = (self.exploration_percent / 100.0) * pw
        self.prog_bar_canvas.create_rectangle(0, 0, fill_w, ph, fill=COLOR_CYAN, outline="")
        self.prog_bar_canvas.create_text(pw // 2, ph // 2, text=f"{int(self.exploration_percent)}% EXPLORED",
                                         font=("Consolas", 8, "bold"), fill=COLOR_TEXT_PRIMARY)

        phase_txt = "CORRIDOR MAPPING" if self.survivors_located_count < 6 else "RAPID EXIT RUN"
        self.prog_stats_lbl.config(
            text=f"ARENA EXPLORED: {int(self.exploration_percent)}%  |  DISTANCE: {self.distance_traversed:.1f}m\n"
                 f"PHASE: {phase_txt}  |  TARGETS: {self.survivors_located_count} / 6 FOUND"
        )

    def _log_event(self, message):
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {message}\n")
        self.log_text.see(tk.END)

    # --------------------------------------------------------------------------
    # ACTION CONTROLS
    # --------------------------------------------------------------------------
    def _start_mission(self):
        if not self.is_mission_active:
            self.is_mission_active = True
            self.start_time = time.time()
            self._log_event("[MISSION] Autonomous Takeoff Initialized -> Target Cruise Altitude: 1.20m")
            self._log_event("[NAV] Traversed Corridor Exploration Active (Frontier SLAM)")
            self.btn_start.config(text="MISSION ACTIVE", bg=COLOR_AMBER)

    def _emergency_abort(self):
        self.is_mission_active = False
        self._log_event("[ALERT] EMERGENCY ABORT (RTL) TRIGGERED BY PILOT!")
        self._log_event("[RTL] Safe Return-to-Launch Initiated Along Traversed Path -> Heading to Entry LZ")
        self.btn_start.config(text="START MISSION", bg="#059669")
        AudioAlertSystem.play_sonar_chirp()


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    app_root = tk.Tk()
    app = TeamEdithAirMouseGCS(app_root)
    app_root.mainloop()
