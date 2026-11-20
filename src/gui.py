"""
Smart Campus AI — Decision Support & Automation System
=======================================================
Desktop GUI Application (Tkinter Standard Library)

A native Python desktop interface for the multi-paradigm Smart Campus AI system:
- Tab 1: Service Desk & Campus Spatial Navigation Map (Intake form + Canvas Graph)
- Tab 2: Decision Record & Clearance Document (ANN, Logic, CSP, Search, Official Clearance)
- Tab 3: Execution Log & Cryptographic Audit Trace (Stage timing, JSON trace, SHA-256 hash)

Features:
- 100% Python standard library (no pip dependencies required)
- Strict enterprise design tokens (Light Canvas #F5F4F0, Navy #1F3A5F, semantic colors)
- Preset quick-scenario loaders (Ali Approved, Sara Rejected, Dr. Khan, Nav Only, Error)
- Live interactive campus canvas graph with clickable node selection and route highlighting
- Interactive probability bar charts and timetable matrices

Course: AL2002 – Artificial Intelligence Lab, Fall 2026 (FAST-NUCES)
"""

import sys
import os
import json
import time
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont

# Ensure src is on sys.path
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Import backend modules
from campus_data import (
    CAMPUS_NODES,
    CAMPUS_EDGES,
    VALID_REQUEST_TYPES,
    VALID_ROLES,
    ROOMS,
    TIME_SLOTS,
    GROUPS,
    CSP_CONSTRAINTS,
    get_node_names,
    build_adjacency_list,
)
from preprocessing import preprocess_request
from router import route_request, get_routing_matrix
from ann_module import predict_priority
from logic_kb import check_authorization, KNOWLEDGE_BASE, RULES
from csp_scheduler import schedule_for_user
from search_navigation import select_algorithm, astar, bfs, ucs
from final_response import FinalResponse
from main import run_pipeline, SCENARIOS, _extract_user_key


# ─── COLOR TOKENS ────────────────────────────────────────────────────────
C_CANVAS = "#F5F4F0"       # Background
C_SURFACE = "#FFFFFF"      # Cards & panels
C_SUBTLE = "#EDEBE5"       # Inputs & secondary backgrounds
C_BORDER = "#DDDAD2"       # 1px borders
C_BORDER_DARK = "#C4C0B6"  # Active/strong borders

C_TEXT_PRIMARY = "#1B1A17" # Main text
C_TEXT_SECONDARY = "#5E5B53" # Subtitles, descriptions
C_TEXT_MUTED = "#8A867D"   # Telemetry, codes, hints

C_BRAND = "#1F3A5F"        # Brand Accent Navy
C_BRAND_HOVER = "#162B47"  # Button hover
C_BRAND_TINT = "#E6ECF3"   # Active selection tint

C_SUCCESS = "#2E7D5B"      # Green
C_SUCCESS_BG = "#E5F2EB"
C_DANGER = "#B03A2E"       # Red
C_DANGER_BG = "#F7E3E0"
C_WARNING = "#A8650F"      # Amber
C_WARNING_BG = "#F7EBD8"


class SmartCampusGUI(tk.Tk):
    """
    Main Application Window for the Smart Campus AI System.
    Orchestrates the entire UI layout, state management, and pipeline execution.
    """

    def __init__(self):
        """
        Initialize the Smart Campus AI GUI application.
        Sets up window geometry, styling themes, state variables, and main layout.
        """
        super().__init__()

        self.title("Smart Campus AI — Decision Support & Automation System")
        self.geometry("1320x860")
        self.minsize(1180, 760)
        self.configure(bg=C_CANVAS)

        # Set default font configuration
        self.default_font = tkfont.nametofont("TkDefaultFont")
        self.default_font.configure(family="Segoe UI", size=10)

        # Application state
        self.current_response = None
        self.active_route_nodes = []
        self.hovered_node = None

        # Step-by-step A* visualization state
        self.step_mode = False          # Whether step mode is active
        self.step_index = -1            # Current step (-1 = before first expansion)
        self.step_trace = []            # List of {node, g, h, f} dicts from SearchResult.trace
        self.step_path = []             # Final optimal path
        self.step_explored = set()      # Nodes expanded so far at current step
        self.step_adjacency = build_adjacency_list()  # For computing frontier nodes

        # Build UI layout
        self._configure_styles()
        self._build_top_bar()
        self._build_pipeline_strip()
        self._build_tab_container()

        # Load Scenario 1 by default
        self.load_scenario(1)

    def _configure_styles(self):
        """
        Configure ttk styling tokens to match the professional design specification.
        Sets up buttons, notebooks, entries, comboboxes, and frames.
        """
        style = ttk.Style(self)
        style.theme_use("clam")

        # General notebook tabs styling
        style.configure(
            "TNotebook",
            background=C_CANVAS,
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background=C_SUBTLE,
            foreground=C_TEXT_SECONDARY,
            padding=[16, 7],
            font=("Segoe UI", 10, "bold"),
            borderwidth=1,
            relief="flat",
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", C_SURFACE), ("active", C_BRAND_TINT)],
            foreground=[("selected", C_BRAND), ("active", C_TEXT_PRIMARY)],
        )

        # Standard Combobox styling
        style.configure(
            "TCombobox",
            fieldbackground=C_SURFACE,
            background=C_SUBTLE,
            foreground=C_TEXT_PRIMARY,
            bordercolor=C_BORDER,
            arrowcolor=C_BRAND,
            padding=4,
        )

        # Standard Entry styling
        style.configure(
            "TEntry",
            fieldbackground=C_SURFACE,
            foreground=C_TEXT_PRIMARY,
            bordercolor=C_BORDER,
            padding=4,
        )

    # ─── TOP HEADER & PRESET SCENARIOS ──────────────────────────────────

    def _build_top_bar(self):
        """
        Construct the top header bar containing branding, status indicator,
        and preset scenario quick-loader buttons.
        """
        header_frame = tk.Frame(self, bg=C_SURFACE, height=52, bd=0, highlightthickness=1, highlightbackground=C_BORDER)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        # Left branding
        left_box = tk.Frame(header_frame, bg=C_SURFACE)
        left_box.pack(side=tk.LEFT, padx=14, pady=8)

        # Monogram
        logo_lbl = tk.Label(
            left_box,
            text="SC",
            font=("Consolas", 11, "bold"),
            bg=C_BRAND,
            fg=C_SURFACE,
            padx=7,
            pady=3,
        )
        logo_lbl.pack(side=tk.LEFT, padx=(0, 10))

        title_box = tk.Frame(left_box, bg=C_SURFACE)
        title_box.pack(side=tk.LEFT)

        title_lbl = tk.Label(
            title_box,
            text="Smart Campus AI",
            font=("Segoe UI", 12, "bold"),
            fg=C_TEXT_PRIMARY,
            bg=C_SURFACE,
        )
        title_lbl.pack(side=tk.LEFT)

        sep_lbl = tk.Label(title_box, text=" / ", font=("Segoe UI", 11), fg=C_TEXT_MUTED, bg=C_SURFACE)
        sep_lbl.pack(side=tk.LEFT)

        subtitle_lbl = tk.Label(
            title_box,
            text="Decision Support & Automation System",
            font=("Segoe UI", 10),
            fg=C_TEXT_SECONDARY,
            bg=C_SURFACE,
        )
        subtitle_lbl.pack(side=tk.LEFT)

        # Right Preset Scenario Buttons
        scenario_box = tk.Frame(header_frame, bg=C_SURFACE)
        scenario_box.pack(side=tk.RIGHT, padx=14, pady=8)

        lbl = tk.Label(
            scenario_box,
            text="Preset Scenarios:",
            font=("Consolas", 9, "bold"),
            fg=C_TEXT_MUTED,
            bg=C_SURFACE,
        )
        lbl.pack(side=tk.LEFT, padx=(0, 6))

        scenarios_meta = [
            (1, "1: Full Svc"),
            (2, "2: Rejected"),
            (3, "3: Eligibility"),
            (4, "4: Nav Only"),
            (5, "5: Error"),
            (6, "6: Booking"),
            (7, "7: Urgent"),
        ]

        for s_id, s_title in scenarios_meta:
            btn = tk.Button(
                scenario_box,
                text=s_title,
                font=("Segoe UI", 8, "bold"),
                bg=C_SUBTLE,
                fg=C_TEXT_PRIMARY,
                activebackground=C_BRAND_TINT,
                activeforeground=C_BRAND,
                bd=0,
                padx=8,
                pady=3,
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=C_BORDER,
                command=lambda sid=s_id: self.load_scenario(sid),
            )
            btn.pack(side=tk.LEFT, padx=2)

    # ─── PIPELINE PROGRESS STRIP ────────────────────────────────────────

    def _build_pipeline_strip(self):
        """
        Construct the horizontal 6-station pipeline status strip.
        Shows Ingestion, Router, ANN, Logic, CSP, and Navigation states.
        """
        self.strip_frame = tk.Frame(self, bg=C_SURFACE, bd=0, highlightthickness=1, highlightbackground=C_BORDER)
        self.strip_frame.pack(fill=tk.X, side=tk.TOP, padx=0, pady=(0, 8))

        self.pipeline_cells = []
        station_names = [
            ("01", "Ingestion"),
            ("02", "Router"),
            ("03", "ANN Priority"),
            ("04", "Logic / KB"),
            ("05", "CSP Scheduler"),
            ("06", "Navigation"),
        ]

        for i, (num, name) in enumerate(station_names):
            cell = tk.Frame(self.strip_frame, bg=C_SURFACE, highlightthickness=1, highlightbackground=C_BORDER)
            cell.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)

            top_row = tk.Frame(cell, bg=C_SURFACE)
            top_row.pack(fill=tk.X, padx=8, pady=(4, 1))

            num_lbl = tk.Label(top_row, text=num, font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_SURFACE)
            num_lbl.pack(side=tk.LEFT)

            name_lbl = tk.Label(top_row, text=name, font=("Segoe UI", 9, "bold"), fg=C_TEXT_PRIMARY, bg=C_SURFACE)
            name_lbl.pack(side=tk.LEFT, padx=(4, 0))

            res_lbl = tk.Label(
                cell,
                text="Pending",
                font=("Consolas", 9),
                fg=C_TEXT_MUTED,
                bg=C_SURFACE,
                anchor="w",
            )
            res_lbl.pack(fill=tk.X, padx=8, pady=(0, 5))

            self.pipeline_cells.append({
                "frame": cell,
                "top": top_row,
                "num": num_lbl,
                "name": name_lbl,
                "result": res_lbl,
            })

    def update_pipeline_strip(self, stages):
        """
        Update the visual state of the 6 pipeline stations.

        Args:
            stages: List of dicts representing stage statuses [{'num': '01', 'name': '...', 'result': '...', 'status': 'done'}, ...]
        """
        for i, cell in enumerate(self.pipeline_cells):
            if i < len(stages):
                stage = stages[i]
                res_text = stage.get("result", "")
                status = stage.get("status", "pending")

                cell["result"].config(text=res_text)

                # Color formatting based on station status
                if status == "done":
                    bg = C_SUCCESS_BG
                    border = C_SUCCESS
                    fg_res = C_SUCCESS
                elif status in ["blocked", "failed", "error"]:
                    bg = C_DANGER_BG
                    border = C_DANGER
                    fg_res = C_DANGER
                elif status == "skipped":
                    bg = C_CANVAS
                    border = C_BORDER
                    fg_res = C_TEXT_MUTED
                else: # pending / current
                    bg = C_SURFACE
                    border = C_BORDER
                    fg_res = C_TEXT_MUTED

                cell["frame"].config(bg=bg, highlightbackground=border)
                cell["top"].config(bg=bg)
                cell["num"].config(bg=bg)
                cell["name"].config(bg=bg)
                cell["result"].config(bg=bg, fg=fg_res)
            else:
                cell["frame"].config(bg=C_SURFACE, highlightbackground=C_BORDER)
                cell["top"].config(bg=C_SURFACE)
                cell["num"].config(bg=C_SURFACE)
                cell["name"].config(bg=C_SURFACE)
                cell["result"].config(bg=C_SURFACE, fg=C_TEXT_MUTED, text="—")

    # ─── TAB NOTEBOOK CONTAINER ─────────────────────────────────────────

    def _build_tab_container(self):
        """
        Construct the central tab container with Notebook tabs:
        - Tab 1: Service Desk & Spatial Map
        - Tab 2: Multi-Paradigm Decision Record & Clearance Document
        - Tab 3: Execution Log & Audit Trace
        """
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        # Create Tab Frames
        self.tab_service_desk = tk.Frame(self.notebook, bg=C_CANVAS)
        self.tab_decision_record = tk.Frame(self.notebook, bg=C_CANVAS)
        self.tab_audit_log = tk.Frame(self.notebook, bg=C_CANVAS)

        self.notebook.add(self.tab_service_desk, text="  1: Service Desk & Campus Map  ")
        self.notebook.add(self.tab_decision_record, text="  2: Decision Record & Clearance  ")
        self.notebook.add(self.tab_audit_log, text="  3: Execution Log & Audit Trace  ")

        # Initialize content for all tabs
        self._init_service_desk_tab()
        self._init_decision_record_tab()
        self._init_audit_log_tab()

    # ─── TAB 1: SERVICE DESK & SPATIAL MAP ──────────────────────────────

    def _init_service_desk_tab(self):
        """Initialize the Service Desk tab: Intake Form on left, Campus Map on right."""
        container = tk.Frame(self.tab_service_desk, bg=C_CANVAS)
        container.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Left Column: Structured Intake Form (~380px)
        self.form_frame = tk.Frame(
            container,
            bg=C_SURFACE,
            width=380,
            highlightthickness=1,
            highlightbackground=C_BORDER,
        )
        self.form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8), pady=0)
        self.form_frame.pack_propagate(False)

        # Right Column: Campus Spatial Graph
        self.map_container = tk.Frame(
            container,
            bg=C_SURFACE,
            highlightthickness=1,
            highlightbackground=C_BORDER,
        )
        self.map_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0)

        self._build_intake_form()
        self._build_campus_canvas()

    def _build_intake_form(self):
        """Construct the form controls for structured user request input."""
        f = self.form_frame

        # Header
        header = tk.Frame(f, bg=C_SURFACE)
        header.pack(fill=tk.X, padx=14, pady=(12, 8))
        tk.Label(
            header,
            text="Structured Request Intake",
            font=("Segoe UI", 12, "bold"),
            fg=C_TEXT_PRIMARY,
            bg=C_SURFACE,
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Standardized university operations request schema",
            font=("Segoe UI", 8),
            fg=C_TEXT_SECONDARY,
            bg=C_SURFACE,
        ).pack(anchor="w")

        # User Name and Roll Number
        user_grid = tk.Frame(f, bg=C_SURFACE)
        user_grid.pack(fill=tk.X, padx=14, pady=4)

        tk.Label(user_grid, text="Subject Name", font=("Segoe UI", 9, "bold"), fg=C_TEXT_SECONDARY, bg=C_SURFACE).grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.ent_name = ttk.Entry(user_grid, width=18)
        self.ent_name.grid(row=1, column=0, sticky="w", padx=(0, 6))

        tk.Label(user_grid, text="Roll Number", font=("Segoe UI", 9, "bold"), fg=C_TEXT_SECONDARY, bg=C_SURFACE).grid(row=0, column=1, sticky="w", pady=(0, 2))
        self.ent_roll = ttk.Entry(user_grid, width=14)
        self.ent_roll.grid(row=1, column=1, sticky="w")

        # User Role
        role_frame = tk.Frame(f, bg=C_SURFACE)
        role_frame.pack(fill=tk.X, padx=14, pady=6)
        tk.Label(role_frame, text="User Role", font=("Segoe UI", 9, "bold"), fg=C_TEXT_SECONDARY, bg=C_SURFACE).pack(anchor="w", pady=(0, 2))

        self.var_role = tk.StringVar(value="Student")
        role_btn_box = tk.Frame(role_frame, bg=C_SUBTLE, padx=2, pady=2, highlightthickness=1, highlightbackground=C_BORDER)
        role_btn_box.pack(fill=tk.X)

        for r in ["Student", "Instructor", "Staff"]:
            rb = tk.Radiobutton(
                role_btn_box,
                text=r,
                value=r,
                variable=self.var_role,
                font=("Segoe UI", 9),
                bg=C_SUBTLE,
                fg=C_TEXT_PRIMARY,
                activebackground=C_BRAND_TINT,
                selectcolor=C_SURFACE,
                indicatoron=False,
                bd=0,
                padx=10,
                pady=3,
                cursor="hand2",
            )
            rb.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Request Type
        req_type_frame = tk.Frame(f, bg=C_SURFACE)
        req_type_frame.pack(fill=tk.X, padx=14, pady=6)
        tk.Label(req_type_frame, text="Request Type & Target Pipeline", font=("Segoe UI", 9, "bold"), fg=C_TEXT_SECONDARY, bg=C_SURFACE).pack(anchor="w", pady=(0, 2))

        self.var_req_type = tk.StringVar(value="Full_Service_Request")
        self.cmb_req_type = ttk.Combobox(
            req_type_frame,
            textvariable=self.var_req_type,
            values=VALID_REQUEST_TYPES,
            state="readonly",
        )
        self.cmb_req_type.pack(fill=tk.X)
        self.cmb_req_type.bind("<<ComboboxSelected>>", self._on_req_type_changed)

        self.lbl_route_hint = tk.Label(
            req_type_frame,
            text="Target Pipeline: ANN → Logic → CSP → Search",
            font=("Consolas", 8),
            fg=C_BRAND,
            bg=C_SURFACE,
        )
        self.lbl_route_hint.pack(anchor="w", pady=(2, 0))

        # Origin & Destination Landmarks
        nodes = get_node_names()
        loc_grid = tk.Frame(f, bg=C_SURFACE)
        loc_grid.pack(fill=tk.X, padx=14, pady=6)

        tk.Label(loc_grid, text="Origin Node", font=("Segoe UI", 9, "bold"), fg=C_TEXT_SECONDARY, bg=C_SURFACE).grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.cmb_origin = ttk.Combobox(loc_grid, values=nodes, width=16, state="readonly")
        self.cmb_origin.grid(row=1, column=0, sticky="w", padx=(0, 6))
        self.cmb_origin.set("Main_Gate")
        self.cmb_origin.bind("<<ComboboxSelected>>", lambda e: self.execute_pipeline_from_form())

        tk.Label(loc_grid, text="Destination Node", font=("Segoe UI", 9, "bold"), fg=C_TEXT_SECONDARY, bg=C_SURFACE).grid(row=0, column=1, sticky="w", pady=(0, 2))
        self.cmb_dest = ttk.Combobox(loc_grid, values=nodes, width=16, state="readonly")
        self.cmb_dest.grid(row=1, column=1, sticky="w")
        self.cmb_dest.set("AI_Lab")
        self.cmb_dest.bind("<<ComboboxSelected>>", lambda e: self.execute_pipeline_from_form())

        # Severity Rating Slider
        sev_frame = tk.Frame(f, bg=C_SURFACE)
        sev_frame.pack(fill=tk.X, padx=14, pady=6)

        sev_header = tk.Frame(sev_frame, bg=C_SURFACE)
        sev_header.pack(fill=tk.X)
        tk.Label(sev_header, text="Severity Rating (0.0 - 10.0)", font=("Segoe UI", 9, "bold"), fg=C_TEXT_SECONDARY, bg=C_SURFACE).pack(side=tk.LEFT)
        self.lbl_sev_val = tk.Label(sev_header, text="8.5 / 10", font=("Consolas", 9, "bold"), fg=C_BRAND, bg=C_SURFACE)
        self.lbl_sev_val.pack(side=tk.RIGHT)

        self.scale_sev = ttk.Scale(
            sev_frame,
            from_=0.0,
            to=10.0,
            value=8.5,
            command=lambda v: self.lbl_sev_val.config(text=f"{float(v):.1f} / 10"),
        )
        self.scale_sev.pack(fill=tk.X, pady=(2, 0))

        # Time Sensitivity Slider
        time_frame = tk.Frame(f, bg=C_SURFACE)
        time_frame.pack(fill=tk.X, padx=14, pady=6)

        time_header = tk.Frame(time_frame, bg=C_SURFACE)
        time_header.pack(fill=tk.X)
        tk.Label(time_header, text="Time Sensitivity (0.0 - 1.0)", font=("Segoe UI", 9, "bold"), fg=C_TEXT_SECONDARY, bg=C_SURFACE).pack(side=tk.LEFT)
        self.lbl_time_val = tk.Label(time_header, text="0.92", font=("Consolas", 9, "bold"), fg=C_BRAND, bg=C_SURFACE)
        self.lbl_time_val.pack(side=tk.RIGHT)

        self.scale_time = ttk.Scale(
            time_frame,
            from_=0.0,
            to=1.0,
            value=0.92,
            command=lambda v: self.lbl_time_val.config(text=f"{float(v):.2f}"),
        )
        self.scale_time.pack(fill=tk.X, pady=(2, 0))

        # Derived Context Telemetry (Crowd level, Physical distance)
        context_box = tk.Frame(f, bg=C_SUBTLE, padx=8, pady=6, highlightthickness=1, highlightbackground=C_BORDER)
        context_box.pack(fill=tk.X, padx=14, pady=8)

        self.lbl_derived_crowd = tk.Label(context_box, text="Est. Crowd Level: 0.40 (Moderate)", font=("Consolas", 8), fg=C_TEXT_SECONDARY, bg=C_SUBTLE)
        self.lbl_derived_crowd.pack(anchor="w")

        self.lbl_derived_dist = tk.Label(context_box, text="Direct Spatial Distance: 0.32 (~320m)", font=("Consolas", 8), fg=C_TEXT_SECONDARY, bg=C_SUBTLE)
        self.lbl_derived_dist.pack(anchor="w")

        # Action Buttons
        btn_box = tk.Frame(f, bg=C_SURFACE)
        btn_box.pack(fill=tk.X, padx=14, pady=(10, 14))

        self.btn_run = tk.Button(
            btn_box,
            text="▶  RUN AI PIPELINE",
            font=("Segoe UI", 10, "bold"),
            bg=C_BRAND,
            fg=C_SURFACE,
            activebackground=C_BRAND_HOVER,
            activeforeground=C_SURFACE,
            bd=0,
            pady=8,
            cursor="hand2",
            command=self.execute_pipeline_from_form,
        )
        self.btn_run.pack(fill=tk.X, pady=(0, 6))

        btn_reset = tk.Button(
            btn_box,
            text="↺ Reset Form Fields",
            font=("Segoe UI", 9),
            bg=C_SUBTLE,
            fg=C_TEXT_SECONDARY,
            activebackground=C_BORDER,
            bd=0,
            pady=4,
            cursor="hand2",
            command=lambda: self.load_scenario(1),
        )
        btn_reset.pack(fill=tk.X)

    def _on_req_type_changed(self, event=None):
        """Update pipeline routing hint when request type dropdown changes."""
        req_type = self.var_req_type.get()
        router_res = route_request(req_type)
        pipe_str = " → ".join(router_res.pipeline)
        self.lbl_route_hint.config(text=f"Target Pipeline: {pipe_str}")

    def _build_campus_canvas(self):
        """Construct the interactive Tkinter Canvas for the 13-node campus spatial graph."""
        c = self.map_container

        # Title and legend header
        map_header = tk.Frame(c, bg=C_SURFACE)
        map_header.pack(fill=tk.X, padx=14, pady=(10, 6))

        title_box = tk.Frame(map_header, bg=C_SURFACE)
        title_box.pack(side=tk.LEFT)
        tk.Label(title_box, text="Campus Spatial Navigation Graph", font=("Segoe UI", 12, "bold"), fg=C_TEXT_PRIMARY, bg=C_SURFACE).pack(anchor="w")
        tk.Label(title_box, text="13 Geodetic Landmarks · 19 Weighted Connections · A* Pathfinding", font=("Segoe UI", 8), fg=C_TEXT_SECONDARY, bg=C_SURFACE).pack(anchor="w")

        legend_box = tk.Frame(map_header, bg=C_SURFACE)
        legend_box.pack(side=tk.RIGHT)
        tk.Label(legend_box, text="● Landmark", font=("Segoe UI", 9), fg=C_TEXT_MUTED, bg=C_SURFACE).pack(side=tk.LEFT, padx=4)
        tk.Label(legend_box, text="● Origin", font=("Segoe UI", 9, "bold"), fg=C_BRAND, bg=C_SURFACE).pack(side=tk.LEFT, padx=4)
        tk.Label(legend_box, text="● Target", font=("Segoe UI", 9, "bold"), fg=C_WARNING, bg=C_SURFACE).pack(side=tk.LEFT, padx=4)
        tk.Label(legend_box, text="━ Active Route", font=("Segoe UI", 9, "bold"), fg=C_BRAND, bg=C_SURFACE).pack(side=tk.LEFT, padx=4)
        tk.Label(legend_box, text="● Expanded", font=("Segoe UI", 9), fg=C_SUCCESS, bg=C_SURFACE).pack(side=tk.LEFT, padx=4)
        tk.Label(legend_box, text="● Current", font=("Segoe UI", 9, "bold"), fg="#D9822B", bg=C_SURFACE).pack(side=tk.LEFT, padx=4)
        tk.Label(legend_box, text="○ Frontier", font=("Segoe UI", 9), fg="#4A90D9", bg=C_SURFACE).pack(side=tk.LEFT, padx=4)

        # The interactive Canvas
        self.canvas_map = tk.Canvas(
            c,
            bg=C_CANVAS,
            bd=0,
            highlightthickness=1,
            highlightbackground=C_BORDER,
        )
        self.canvas_map.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)
        self.canvas_map.bind("<Configure>", lambda e: self._on_canvas_resize())
        self.canvas_map.bind("<Button-1>", self._on_canvas_click)
        self.canvas_map.bind("<Button-3>", self._on_canvas_right_click)
        self.canvas_map.bind("<Motion>", self._on_canvas_hover)

        # ── A* Step-by-Step Control Bar ──
        self.step_bar = tk.Frame(c, bg=C_SUBTLE, padx=6, pady=4,
                                 highlightthickness=1, highlightbackground=C_BORDER)
        self.step_bar.pack(fill=tk.X, padx=14, pady=(0, 2))

        tk.Label(self.step_bar, text="A* Walkthrough",
                 font=("Segoe UI", 9, "bold"), fg=C_BRAND, bg=C_SUBTLE).pack(side=tk.LEFT, padx=(0, 10))

        self.btn_step_reset = tk.Button(
            self.step_bar, text="⏮ Reset", font=("Segoe UI", 8), bg=C_SURFACE, fg=C_TEXT_PRIMARY,
            activebackground=C_BORDER, bd=1, relief="solid", padx=8, pady=2, cursor="hand2",
            command=self._step_reset, state="disabled")
        self.btn_step_reset.pack(side=tk.LEFT, padx=2)

        self.btn_step_back = tk.Button(
            self.step_bar, text="◀ Back", font=("Segoe UI", 8), bg=C_SURFACE, fg=C_TEXT_PRIMARY,
            activebackground=C_BORDER, bd=1, relief="solid", padx=8, pady=2, cursor="hand2",
            command=self._step_back, state="disabled")
        self.btn_step_back.pack(side=tk.LEFT, padx=2)

        self.btn_step_next = tk.Button(
            self.step_bar, text="▶ Next", font=("Segoe UI", 8, "bold"), bg=C_BRAND, fg=C_SURFACE,
            activebackground=C_BRAND_HOVER, bd=0, padx=10, pady=2, cursor="hand2",
            command=self._step_next, state="disabled")
        self.btn_step_next.pack(side=tk.LEFT, padx=2)

        self.btn_step_play_all = tk.Button(
            self.step_bar, text="⏩ Play All", font=("Segoe UI", 8), bg=C_SURFACE, fg=C_BRAND,
            activebackground=C_BRAND_TINT, bd=1, relief="solid", padx=8, pady=2, cursor="hand2",
            command=self._step_play_all, state="disabled")
        self.btn_step_play_all.pack(side=tk.LEFT, padx=2)

        # Step counter label
        self.lbl_step_counter = tk.Label(
            self.step_bar, text="Step 0 / 0", font=("Consolas", 9, "bold"),
            fg=C_TEXT_SECONDARY, bg=C_SUBTLE)
        self.lbl_step_counter.pack(side=tk.LEFT, padx=(12, 0))

        # Step detail: f(n), g(n), h(n) for current expansion
        self.lbl_step_detail = tk.Label(
            self.step_bar, text="Run a scenario with Search to begin",
            font=("Consolas", 8), fg=C_TEXT_MUTED, bg=C_SUBTLE)
        self.lbl_step_detail.pack(side=tk.RIGHT, padx=(0, 4))

        # Telemetry footer
        self.map_telemetry = tk.Frame(c, bg=C_SURFACE)
        self.map_telemetry.pack(fill=tk.X, padx=14, pady=(6, 10))

        self.lbl_nav_alg = tk.Label(self.map_telemetry, text="Algorithm: A* Search", font=("Consolas", 8, "bold"), fg=C_TEXT_PRIMARY, bg=C_SURFACE)
        self.lbl_nav_alg.pack(side=tk.LEFT, padx=(0, 16))

        self.lbl_nav_cost = tk.Label(self.map_telemetry, text="Cost: 6.0 units (3 edges)", font=("Consolas", 8, "bold"), fg=C_BRAND, bg=C_SURFACE)
        self.lbl_nav_cost.pack(side=tk.LEFT, padx=(0, 16))

        self.lbl_nav_heuristic = tk.Label(self.map_telemetry, text="Heuristic: Euclidean ÷ 3", font=("Consolas", 8), fg=C_TEXT_SECONDARY, bg=C_SURFACE)
        self.lbl_nav_heuristic.pack(side=tk.LEFT, padx=(0, 16))

        self.lbl_nav_time = tk.Label(self.map_telemetry, text="Latency: 0.11 ms", font=("Consolas", 8), fg=C_SUCCESS, bg=C_SURFACE)
        self.lbl_nav_time.pack(side=tk.RIGHT)

    def _get_canvas_coords(self, node_name, width, height):
        """
        Convert campus node coordinates (x: 0..10, y: 0..5) to canvas pixel coordinates.

        Args:
            node_name: Name of the landmark node
            width: Canvas width in pixels
            height: Canvas height in pixels

        Returns:
            Tuple (px, py) in canvas coordinates
        """
        node = CAMPUS_NODES[node_name]
        nx = node["x"]
        ny = node["y"]

        margin_x = 75
        margin_y = 65
        plot_w = max(100, width - 2 * margin_x)
        plot_h = max(100, height - 2 * margin_y)

        # Invert y so Admin_Block (y=5) is at top and Hostel (y=0) is at bottom
        px = margin_x + (nx / 10.0) * plot_w
        py = margin_y + ((5.0 - ny) / 5.0) * plot_h
        return px, py

    def _on_canvas_resize(self):
        """Handle canvas resize: redraw using stepped mode if active, else normal mode."""
        if self.step_mode and self.step_index >= 0:
            self._redraw_campus_graph_stepped()
        else:
            self._redraw_campus_graph()

    def _redraw_campus_graph(self):
        """Redraw all 13 nodes, 19 edges, and the active route on the canvas."""
        canvas = self.canvas_map
        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 10 or height <= 10:
            return

        origin = self.cmb_origin.get()
        destination = self.cmb_dest.get()
        route = self.active_route_nodes

        # Identify route edges
        route_edges = set()
        if len(route) >= 2:
            for idx in range(len(route) - 1):
                u, v = route[idx], route[idx + 1]
                route_edges.add((u, v))
                route_edges.add((v, u))

        # 1. Draw inactive edges first
        for u, v, w in CAMPUS_EDGES:
            if (u, v) in route_edges:
                continue
            x1, y1 = self._get_canvas_coords(u, width, height)
            x2, y2 = self._get_canvas_coords(v, width, height)

            canvas.create_line(x1, y1, x2, y2, fill=C_BORDER_DARK, width=1.5, dash=(4, 3))

            # Draw weight badge
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            canvas.create_rectangle(mx - 8, my - 6, mx + 8, my + 6, fill=C_CANVAS, outline=C_BORDER)
            canvas.create_text(mx, my, text=str(w), font=("Consolas", 8), fill=C_TEXT_MUTED)

        # 2. Draw active route edges (highlighted)
        if len(route) >= 2:
            for idx in range(len(route) - 1):
                u, v = route[idx], route[idx + 1]
                x1, y1 = self._get_canvas_coords(u, width, height)
                x2, y2 = self._get_canvas_coords(v, width, height)

                # Bold Navy route line
                canvas.create_line(x1, y1, x2, y2, fill=C_BRAND, width=3.5, capstyle=tk.ROUND)

                # Active weight badge
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                # Look up weight
                w = next((edge[2] for edge in CAMPUS_EDGES if (edge[0] == u and edge[1] == v) or (edge[0] == v and edge[1] == u)), 1)
                canvas.create_rectangle(mx - 9, my - 7, mx + 9, my + 7, fill=C_BRAND, outline=C_BRAND)
                canvas.create_text(mx, my, text=str(w), font=("Consolas", 8, "bold"), fill=C_SURFACE)

        # 3. Draw nodes
        self.node_hitboxes = {}
        for name in CAMPUS_NODES:
            px, py = self._get_canvas_coords(name, width, height)
            is_origin = (name == origin)
            is_dest = (name == destination)
            is_in_route = (name in route)

            r = 8
            self.node_hitboxes[name] = (px, py, r + 4)

            # Node halo / highlight rings
            if is_dest:
                canvas.create_oval(px - 14, py - 14, px + 14, py + 14, outline=C_WARNING, width=2, dash=(2, 2))
            elif is_origin:
                canvas.create_oval(px - 14, py - 14, px + 14, py + 14, outline=C_BRAND, width=1.5)

            # Main Node circle
            if is_in_route or is_origin:
                fill_color = C_BRAND
                outline_color = C_BRAND
                txt_color = C_BRAND
            elif is_dest:
                fill_color = C_WARNING
                outline_color = C_WARNING
                txt_color = C_WARNING
            else:
                fill_color = C_SURFACE
                outline_color = C_BORDER_DARK
                txt_color = C_TEXT_SECONDARY

            canvas.create_oval(px - r, py - r, px + r, py + r, fill=fill_color, outline=outline_color, width=2)

            if fill_color == C_SURFACE:
                canvas.create_oval(px - 2, py - 2, px + 2, py + 2, fill=C_BORDER_DARK, outline="")

            # Node label
            # Position label above or below depending on coordinate
            y_offset = -14 if CAMPUS_NODES[name]["y"] >= 4 else 15
            canvas.create_text(
                px,
                py + y_offset,
                text=name.replace("_", " "),
                font=("Consolas", 8, "bold" if is_in_route else "normal"),
                fill=txt_color,
            )

    def _find_node_at_pos(self, x, y):
        """Return the name of the campus node at pixel (x, y) if clicked, or None."""
        if not hasattr(self, "node_hitboxes"):
            return None
        for name, (px, py, r) in self.node_hitboxes.items():
            if (x - px) ** 2 + (y - py) ** 2 <= (r + 4) ** 2:
                return name
        return None

    def _on_canvas_click(self, event):
        """Handle left-click on canvas: select node as Destination and re-run route."""
        clicked_node = self._find_node_at_pos(event.x, event.y)
        if clicked_node:
            self.cmb_dest.set(clicked_node)
            self.execute_pipeline_from_form()

    def _on_canvas_right_click(self, event):
        """Handle right-click on canvas: select node as Origin and re-run route."""
        clicked_node = self._find_node_at_pos(event.x, event.y)
        if clicked_node:
            self.cmb_origin.set(clicked_node)
            self.execute_pipeline_from_form()

    def _on_canvas_hover(self, event):
        """Handle mouse hover to show node description tooltip in the bottom telemetry."""
        node_name = self._find_node_at_pos(event.x, event.y)
        if node_name and node_name != self.hovered_node:
            self.hovered_node = node_name
            meta = CAMPUS_NODES[node_name]
            self.lbl_nav_heuristic.config(
                text=f"{node_name}: ({meta['x']}, {meta['y']}) · {meta['description']}"
            )
        elif not node_name and self.hovered_node:
            self.hovered_node = None
            self.lbl_nav_heuristic.config(text="Heuristic: Euclidean ÷ 3 (admissible, consistent)")

    # ─── A* STEP-BY-STEP VISUALIZATION ──────────────────────────────────

    def _init_step_mode(self):
        """
        Initialize step-by-step mode from the current search result.
        Populates the step trace data and enables the walkthrough controls.
        Called after pipeline execution produces a SearchResult with a trace.
        """
        resp = self.current_response
        if not resp or not resp.search_result or not resp.search_result.trace:
            self._disable_step_controls()
            return

        self.step_trace = resp.search_result.trace      # [{node, g, h, f}, ...]
        self.step_path = resp.search_result.path or []   # Final optimal path
        self.step_index = -1                              # Before first expansion
        self.step_explored = set()
        self.step_mode = True

        total = len(self.step_trace)
        self.lbl_step_counter.config(text=f"Step 0 / {total}")
        self.lbl_step_detail.config(text="Press ▶ Next to begin A* expansion walkthrough")

        # Enable controls
        self.btn_step_next.config(state="normal")
        self.btn_step_play_all.config(state="normal")
        self.btn_step_reset.config(state="normal")
        self.btn_step_back.config(state="disabled")

    def _disable_step_controls(self):
        """Disable all step walkthrough controls when no search trace is available."""
        self.step_mode = False
        self.step_index = -1
        self.step_trace = []
        self.step_path = []
        self.step_explored = set()
        self.btn_step_next.config(state="disabled")
        self.btn_step_back.config(state="disabled")
        self.btn_step_play_all.config(state="disabled")
        self.btn_step_reset.config(state="disabled")
        self.lbl_step_counter.config(text="Step 0 / 0")
        self.lbl_step_detail.config(text="Run a scenario with Search to begin")

    def _step_next(self):
        """
        Advance the A* visualization by one expansion step.
        Adds the next node to the explored set and redraws the graph.
        """
        if not self.step_mode or not self.step_trace:
            return

        total = len(self.step_trace)
        if self.step_index < total - 1:
            self.step_index += 1
            entry = self.step_trace[self.step_index]
            self.step_explored.add(entry["node"])

            # Update counter and detail labels
            self.lbl_step_counter.config(text=f"Step {self.step_index + 1} / {total}")
            self.lbl_step_detail.config(
                text=f"Expanding: {entry['node']}  |  "
                     f"f({entry['node']}) = g({entry['g']}) + h({entry['h']}) = {entry['f']}"
            )

            # Update button states
            self.btn_step_back.config(state="normal")
            if self.step_index >= total - 1:
                self.btn_step_next.config(state="disabled")
                self.btn_step_play_all.config(state="disabled")
                # At last step show final path
                self.lbl_step_detail.config(
                    text=f"Goal reached: {entry['node']}  |  "
                         f"Optimal cost = {entry['g']}  |  "
                         f"Path: {' → '.join(self.step_path)}"
                )

            self._redraw_campus_graph_stepped()

    def _step_back(self):
        """
        Rewind the A* visualization by one expansion step.
        Removes the most recently expanded node and redraws.
        """
        if not self.step_mode or self.step_index < 0:
            return

        # Remove current node from explored
        entry = self.step_trace[self.step_index]
        self.step_explored.discard(entry["node"])
        self.step_index -= 1

        total = len(self.step_trace)

        if self.step_index >= 0:
            prev_entry = self.step_trace[self.step_index]
            self.lbl_step_counter.config(text=f"Step {self.step_index + 1} / {total}")
            self.lbl_step_detail.config(
                text=f"Expanding: {prev_entry['node']}  |  "
                     f"f({prev_entry['node']}) = g({prev_entry['g']}) + h({prev_entry['h']}) = {prev_entry['f']}"
            )
        else:
            self.lbl_step_counter.config(text=f"Step 0 / {total}")
            self.lbl_step_detail.config(text="Press ▶ Next to begin A* expansion walkthrough")

        # Update button states
        self.btn_step_next.config(state="normal")
        self.btn_step_play_all.config(state="normal")
        if self.step_index < 0:
            self.btn_step_back.config(state="disabled")

        self._redraw_campus_graph_stepped()

    def _step_play_all(self):
        """
        Jump to the final step showing the complete optimal route.
        Equivalent to pressing Next until the end.
        """
        if not self.step_mode or not self.step_trace:
            return

        total = len(self.step_trace)
        self.step_index = total - 1

        # Mark all trace nodes as explored
        self.step_explored = set()
        for entry in self.step_trace:
            self.step_explored.add(entry["node"])

        last = self.step_trace[-1]
        self.lbl_step_counter.config(text=f"Step {total} / {total}")
        self.lbl_step_detail.config(
            text=f"Complete  |  Optimal cost = {last['g']}  |  "
                 f"Path: {' → '.join(self.step_path)}"
        )

        # Disable forward, enable back
        self.btn_step_next.config(state="disabled")
        self.btn_step_play_all.config(state="disabled")
        self.btn_step_back.config(state="normal")

        self._redraw_campus_graph_stepped()

    def _step_reset(self):
        """
        Reset the A* visualization to the initial state (before first expansion).
        Shows only origin and destination with no expansions.
        """
        if not self.step_mode or not self.step_trace:
            return

        self.step_index = -1
        self.step_explored = set()

        total = len(self.step_trace)
        self.lbl_step_counter.config(text=f"Step 0 / {total}")
        self.lbl_step_detail.config(text="Press ▶ Next to begin A* expansion walkthrough")

        # Reset button states
        self.btn_step_next.config(state="normal")
        self.btn_step_play_all.config(state="normal")
        self.btn_step_back.config(state="disabled")

        self._redraw_campus_graph_stepped()

    def _compute_frontier_at_step(self):
        """
        Compute the set of frontier nodes at the current step.
        Frontier = neighbors of explored nodes that have not yet been expanded.

        Returns:
            Set of node names that are on the frontier (generated but not expanded).
        """
        frontier = set()
        for explored_node in self.step_explored:
            for neighbor, _weight in self.step_adjacency.get(explored_node, []):
                if neighbor not in self.step_explored:
                    frontier.add(neighbor)
        return frontier

    def _redraw_campus_graph_stepped(self):
        """
        Redraw the campus graph with A* step-by-step coloring.
        Color semantics:
         - Green fill (#2E7D5B):  Previously explored/expanded nodes
         - Orange ring (#D9822B): Current node being expanded (trace[step_index])
         - Light blue outline (#4A90D9): Frontier nodes (generated, not expanded)
         - Navy bold route (#1F3A5F): Final optimal path (shown only at last step)
         - f(n) label: Drawn near the current node being expanded
        """
        canvas = self.canvas_map
        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 10 or height <= 10:
            return

        origin = self.cmb_origin.get()
        destination = self.cmb_dest.get()

        # Determine current node and frontier
        current_node = None
        if 0 <= self.step_index < len(self.step_trace):
            current_node = self.step_trace[self.step_index]["node"]
        frontier = self._compute_frontier_at_step()

        # Show final path only when at the last step
        total = len(self.step_trace)
        at_last_step = (self.step_index >= 0 and self.step_index == total - 1)
        route = self.step_path if at_last_step else []

        # Identify route edges
        route_edges = set()
        if len(route) >= 2:
            for idx in range(len(route) - 1):
                u, v = route[idx], route[idx + 1]
                route_edges.add((u, v))
                route_edges.add((v, u))

        # 1. Draw inactive edges
        for u, v, w in CAMPUS_EDGES:
            if (u, v) in route_edges:
                continue
            x1, y1 = self._get_canvas_coords(u, width, height)
            x2, y2 = self._get_canvas_coords(v, width, height)
            canvas.create_line(x1, y1, x2, y2, fill=C_BORDER_DARK, width=1.5, dash=(4, 3))

            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            canvas.create_rectangle(mx - 8, my - 6, mx + 8, my + 6, fill=C_CANVAS, outline=C_BORDER)
            canvas.create_text(mx, my, text=str(w), font=("Consolas", 8), fill=C_TEXT_MUTED)

        # 2. Draw active route edges (only at last step)
        if len(route) >= 2:
            for idx in range(len(route) - 1):
                u, v = route[idx], route[idx + 1]
                x1, y1 = self._get_canvas_coords(u, width, height)
                x2, y2 = self._get_canvas_coords(v, width, height)

                canvas.create_line(x1, y1, x2, y2, fill=C_BRAND, width=3.5, capstyle=tk.ROUND)

                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                w = next((edge[2] for edge in CAMPUS_EDGES if (edge[0] == u and edge[1] == v) or (edge[0] == v and edge[1] == u)), 1)
                canvas.create_rectangle(mx - 9, my - 7, mx + 9, my + 7, fill=C_BRAND, outline=C_BRAND)
                canvas.create_text(mx, my, text=str(w), font=("Consolas", 8, "bold"), fill=C_SURFACE)

        # 3. Draw nodes with step-mode coloring
        self.node_hitboxes = {}
        for name in CAMPUS_NODES:
            px, py = self._get_canvas_coords(name, width, height)
            is_origin = (name == origin)
            is_dest = (name == destination)
            is_explored = (name in self.step_explored and name != current_node)
            is_current = (name == current_node)
            is_frontier = (name in frontier and name != current_node and name not in self.step_explored)
            is_in_route = (name in route)

            r = 8
            self.node_hitboxes[name] = (px, py, r + 4)

            # Node halo / highlight rings
            if is_current:
                # Orange pulsing ring for current expansion node
                canvas.create_oval(px - 16, py - 16, px + 16, py + 16, outline="#D9822B", width=3)
            elif is_frontier:
                # Light blue dashed ring for frontier nodes
                canvas.create_oval(px - 14, py - 14, px + 14, py + 14, outline="#4A90D9", width=2, dash=(3, 2))
            elif is_dest:
                canvas.create_oval(px - 14, py - 14, px + 14, py + 14, outline=C_WARNING, width=2, dash=(2, 2))
            elif is_origin:
                canvas.create_oval(px - 14, py - 14, px + 14, py + 14, outline=C_BRAND, width=1.5)

            # Main node circle fill color
            if is_current:
                fill_color = "#D9822B"    # Orange — currently expanding
                outline_color = "#D9822B"
                txt_color = "#D9822B"
            elif is_explored:
                fill_color = C_SUCCESS     # Green — already expanded
                outline_color = C_SUCCESS
                txt_color = C_SUCCESS
            elif is_frontier:
                fill_color = "#4A90D9"     # Blue — frontier
                outline_color = "#4A90D9"
                txt_color = "#4A90D9"
            elif is_in_route and at_last_step:
                fill_color = C_BRAND
                outline_color = C_BRAND
                txt_color = C_BRAND
            elif is_dest:
                fill_color = C_WARNING
                outline_color = C_WARNING
                txt_color = C_WARNING
            elif is_origin:
                fill_color = C_BRAND
                outline_color = C_BRAND
                txt_color = C_BRAND
            else:
                fill_color = C_SURFACE
                outline_color = C_BORDER_DARK
                txt_color = C_TEXT_SECONDARY

            canvas.create_oval(px - r, py - r, px + r, py + r, fill=fill_color, outline=outline_color, width=2)

            if fill_color == C_SURFACE:
                canvas.create_oval(px - 2, py - 2, px + 2, py + 2, fill=C_BORDER_DARK, outline="")

            # Node label
            y_offset = -14 if CAMPUS_NODES[name]["y"] >= 4 else 15
            font_weight = "bold" if (is_current or is_explored or is_in_route) else "normal"
            canvas.create_text(px, py + y_offset, text=name.replace("_", " "),
                               font=("Consolas", 8, font_weight), fill=txt_color)

            # f(n) = g(n) + h(n) label near current node
            if is_current and 0 <= self.step_index < len(self.step_trace):
                entry = self.step_trace[self.step_index]
                cost_text = f"f={entry['f']}"
                canvas.create_text(px + 20, py - 20, text=cost_text,
                                   font=("Consolas", 9, "bold"), fill="#D9822B",
                                   anchor="w")

    # ─── TAB 2: DECISION RECORD & CLEARANCE ─────────────────────────────

    def _init_decision_record_tab(self):
        """Initialize Tab 2: The Multi-Paradigm Decision Record & Clearance Card."""
        container = tk.Frame(self.tab_decision_record, bg=C_CANVAS)
        container.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Left Column: The 4 Paradigms (ANN, Logic, CSP, Search)
        self.record_left = tk.Frame(container, bg=C_CANVAS)
        self.record_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # Right Column: Entry Clearance Document Card (~380px)
        self.record_right = tk.Frame(
            container,
            bg=C_SURFACE,
            width=380,
            highlightthickness=1,
            highlightbackground=C_BORDER,
        )
        self.record_right.pack(side=tk.RIGHT, fill=tk.Y)
        self.record_right.pack_propagate(False)

        self._build_paradigm_cards()
        self._build_clearance_card()

    def _build_paradigm_cards(self):
        """Construct cards for ANN, Logic/KB, CSP, and Navigation."""
        parent = self.record_left

        # Scrollable container for cards
        canvas_cards = tk.Canvas(parent, bg=C_CANVAS, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas_cards.yview)
        self.cards_inner = tk.Frame(canvas_cards, bg=C_CANVAS)

        self.cards_inner.bind(
            "<Configure>",
            lambda e: canvas_cards.configure(scrollregion=canvas_cards.bbox("all")),
        )
        canvas_cards.create_window((0, 0), window=self.cards_inner, anchor="nw")
        canvas_cards.configure(yscrollcommand=scrollbar.set)

        canvas_cards.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Card 1: ANN Priority Predictor
        self.card_ann = tk.Frame(self.cards_inner, bg=C_SURFACE, highlightthickness=1, highlightbackground=C_BORDER)
        self.card_ann.pack(fill=tk.X, pady=(0, 8), padx=2)
        self._build_ann_card_content(self.card_ann)

        # Card 2: Logic / Knowledge Base Gatekeeper
        self.card_logic = tk.Frame(self.cards_inner, bg=C_SURFACE, highlightthickness=1, highlightbackground=C_BORDER)
        self.card_logic.pack(fill=tk.X, pady=(0, 8), padx=2)
        self._build_logic_card_content(self.card_logic)

        # Card 3: CSP Scheduler
        self.card_csp = tk.Frame(self.cards_inner, bg=C_SURFACE, highlightthickness=1, highlightbackground=C_BORDER)
        self.card_csp.pack(fill=tk.X, pady=(0, 8), padx=2)
        self._build_csp_card_content(self.card_csp)

        # Card 4: Navigation Recap
        self.card_nav = tk.Frame(self.cards_inner, bg=C_SURFACE, highlightthickness=1, highlightbackground=C_BORDER)
        self.card_nav.pack(fill=tk.X, pady=(0, 8), padx=2)
        self._build_nav_card_content(self.card_nav)

    def _build_ann_card_content(self, card):
        """Build the internal content of the ANN card."""
        header = tk.Frame(card, bg=C_SURFACE)
        header.pack(fill=tk.X, padx=12, pady=(10, 6))

        tk.Label(header, text="01  ANN Priority Predictor", font=("Segoe UI", 11, "bold"), fg=C_TEXT_PRIMARY, bg=C_SURFACE).pack(side=tk.LEFT)
        tk.Label(header, text="(Subsymbolic Modern AI)", font=("Segoe UI", 9), fg=C_TEXT_MUTED, bg=C_SURFACE).pack(side=tk.LEFT, padx=6)

        self.lbl_ann_badge = tk.Label(header, text="URGENT (98.8%)", font=("Consolas", 9, "bold"), fg=C_WARNING, bg=C_WARNING_BG, padx=6, pady=2)
        self.lbl_ann_badge.pack(side=tk.RIGHT)

        body = tk.Frame(card, bg=C_SURFACE)
        body.pack(fill=tk.X, padx=12, pady=(0, 10))

        # Horizontal probability distribution visual bar
        tk.Label(body, text="Probability Distribution (Softmax):", font=("Segoe UI", 9, "bold"), fg=C_TEXT_SECONDARY, bg=C_SURFACE).pack(anchor="w", pady=(2, 2))

        self.canvas_ann_bars = tk.Canvas(body, height=24, bg=C_SUBTLE, bd=0, highlightthickness=1, highlightbackground=C_BORDER)
        self.canvas_ann_bars.pack(fill=tk.X, pady=(0, 4))

        self.lbl_ann_probs_detail = tk.Label(
            body,
            text="Urgent: 98.8% · High: 1.2% · Normal: 0.0% · Low: 0.0%",
            font=("Consolas", 8),
            fg=C_TEXT_SECONDARY,
            bg=C_SURFACE,
        )
        self.lbl_ann_probs_detail.pack(anchor="w")

        # 7-feature vector breakdown
        self.lbl_feature_vec = tk.Label(
            body,
            text="7-Feature Vector: [0.0, 1.0, 0.85, 0.92, 0.40, 0.32, 1.0]",
            font=("Consolas", 8),
            fg=C_TEXT_MUTED,
            bg=C_SUBTLE,
            padx=6,
            pady=3,
        )
        self.lbl_feature_vec.pack(fill=tk.X, pady=(6, 4))

        # Model comparison & policy
        pol_box = tk.Frame(body, bg=C_WARNING_BG, padx=8, pady=4, highlightthickness=1, highlightbackground=C_WARNING)
        pol_box.pack(fill=tk.X, pady=(4, 0))
        tk.Label(
            pol_box,
            text="Policy: ANN predicts urgency class only. It does not grant building access or authorization.",
            font=("Segoe UI", 8, "italic"),
            fg=C_WARNING,
            bg=C_WARNING_BG,
        ).pack(anchor="w")

    def _build_logic_card_content(self, card):
        """Build the internal content of the Logic / Knowledge Base Gatekeeper card."""
        header = tk.Frame(card, bg=C_SURFACE)
        header.pack(fill=tk.X, padx=12, pady=(10, 6))

        tk.Label(header, text="02  Logic / Knowledge Base Gatekeeper", font=("Segoe UI", 11, "bold"), fg=C_TEXT_PRIMARY, bg=C_SURFACE).pack(side=tk.LEFT)
        tk.Label(header, text="(Symbolic Classical AI)", font=("Segoe UI", 9), fg=C_TEXT_MUTED, bg=C_SURFACE).pack(side=tk.LEFT, padx=6)

        self.lbl_logic_badge = tk.Label(header, text="AUTHORIZED", font=("Consolas", 9, "bold"), fg=C_SUCCESS, bg=C_SUCCESS_BG, padx=6, pady=2)
        self.lbl_logic_badge.pack(side=tk.RIGHT)

        body = tk.Frame(card, bg=C_SURFACE)
        body.pack(fill=tk.X, padx=12, pady=(0, 10))

        # Rule Entailment statement
        self.lbl_logic_rules = tk.Label(
            body,
            text="Active Entailment: R1 (Student ∧ Completed PF ⇒ Eligible) ∧ R3 (Enrolled AI ⇒ UsesLab)",
            font=("Consolas", 8),
            fg=C_BRAND,
            bg=C_SUBTLE,
            padx=6,
            pady=3,
        )
        self.lbl_logic_rules.pack(fill=tk.X, pady=(0, 6))

        # Derivation table / reason
        self.lbl_logic_reason = tk.Label(
            body,
            text="Completed(Ali, ProgrammingFundamentals) ∧ Enrolled(Ali, AI) entailed via Modus Ponens.",
            font=("Segoe UI", 9),
            fg=C_TEXT_PRIMARY,
            bg=C_SURFACE,
            wraplength=700,
            justify="left",
        )
        self.lbl_logic_reason.pack(anchor="w", pady=(0, 4))

        # Gatekeeper policy
        gate_box = tk.Frame(body, bg=C_SUBTLE, padx=8, pady=4)
        gate_box.pack(fill=tk.X, pady=(2, 0))
        tk.Label(
            gate_box,
            text="Gatekeeper Policy: If authorization is REJECTED, the pipeline halts immediately. Downstream CSP and Search are never invoked.",
            font=("Segoe UI", 8, "italic"),
            fg=C_TEXT_SECONDARY,
            bg=C_SUBTLE,
        ).pack(anchor="w")

    def _build_csp_card_content(self, card):
        """Build the internal content of the CSP Scheduler card."""
        header = tk.Frame(card, bg=C_SURFACE)
        header.pack(fill=tk.X, padx=12, pady=(10, 6))

        tk.Label(header, text="03  CSP Presentation Scheduler", font=("Segoe UI", 11, "bold"), fg=C_TEXT_PRIMARY, bg=C_SURFACE).pack(side=tk.LEFT)
        tk.Label(header, text="(Constraint Satisfaction)", font=("Segoe UI", 9), fg=C_TEXT_MUTED, bg=C_SURFACE).pack(side=tk.LEFT, padx=6)

        self.lbl_csp_badge = tk.Label(header, text="9/9 CONSTRAINTS SATISFIED", font=("Consolas", 9, "bold"), fg=C_SUCCESS, bg=C_SUCCESS_BG, padx=6, pady=2)
        self.lbl_csp_badge.pack(side=tk.RIGHT)

        body = tk.Frame(card, bg=C_SURFACE)
        body.pack(fill=tk.X, padx=12, pady=(0, 10))

        # Schedule matrix grid
        self.csp_table_frame = tk.Frame(body, bg=C_BORDER, padx=1, pady=1)
        self.csp_table_frame.pack(fill=tk.X, pady=(0, 6))

        self.csp_cells = {}
        # Timetable headers
        rooms = ["Lab 1", "Lab 2", "Lab 3"]
        slots = ["09:00", "10:00", "11:00", "12:00"]

        # Corner header
        tk.Label(self.csp_table_frame, text="Room \\ Slot", font=("Consolas", 8, "bold"), bg=C_SUBTLE, fg=C_TEXT_SECONDARY, padx=6, pady=4).grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        for c_idx, slot in enumerate(slots):
            tk.Label(self.csp_table_frame, text=slot, font=("Consolas", 8, "bold"), bg=C_SUBTLE, fg=C_TEXT_SECONDARY, padx=6, pady=4).grid(row=0, column=c_idx + 1, sticky="nsew", padx=1, pady=1)

        for r_idx, room in enumerate(rooms):
            tk.Label(self.csp_table_frame, text=room, font=("Consolas", 8, "bold"), bg=C_SUBTLE, fg=C_TEXT_PRIMARY, padx=6, pady=4).grid(row=r_idx + 1, column=0, sticky="nsew", padx=1, pady=1)
            for c_idx, slot in enumerate(slots):
                lbl = tk.Label(self.csp_table_frame, text="—", font=("Consolas", 8), bg=C_SURFACE, fg=C_TEXT_MUTED, padx=6, pady=4)
                lbl.grid(row=r_idx + 1, column=c_idx + 1, sticky="nsew", padx=1, pady=1)
                self.csp_cells[(room, slot)] = lbl

        # Configure column weight
        for col in range(5):
            self.csp_table_frame.columnconfigure(col, weight=1)

        self.lbl_csp_assigned = tk.Label(
            body,
            text="Assigned: Group G3 → Lab 1 @ 10:00 (Precedence G4 < G3 satisfied)",
            font=("Consolas", 8),
            fg=C_BRAND,
            bg=C_SURFACE,
        )
        self.lbl_csp_assigned.pack(anchor="w")

    def _build_nav_card_content(self, card):
        """Build the internal content of the Navigation Guidance card."""
        header = tk.Frame(card, bg=C_SURFACE)
        header.pack(fill=tk.X, padx=12, pady=(10, 6))

        tk.Label(header, text="04  Navigation Guidance Recap", font=("Segoe UI", 11, "bold"), fg=C_TEXT_PRIMARY, bg=C_SURFACE).pack(side=tk.LEFT)
        tk.Label(header, text="(A* Pathfinding)", font=("Segoe UI", 9), fg=C_TEXT_MUTED, bg=C_SURFACE).pack(side=tk.LEFT, padx=6)

        self.lbl_nav_badge = tk.Label(header, text="OPTIMAL (Cost 6.0)", font=("Consolas", 9, "bold"), fg=C_BRAND, bg=C_BRAND_TINT, padx=6, pady=2)
        self.lbl_nav_badge.pack(side=tk.RIGHT)

        body = tk.Frame(card, bg=C_SURFACE)
        body.pack(fill=tk.X, padx=12, pady=(0, 10))

        self.lbl_nav_path_text = tk.Label(
            body,
            text="Main_Gate → (2) → Parking → (3) → Science_Block → (1) → AI_Lab",
            font=("Consolas", 9, "bold"),
            fg=C_TEXT_PRIMARY,
            bg=C_SUBTLE,
            padx=8,
            pady=6,
            anchor="w",
        )
        self.lbl_nav_path_text.pack(fill=tk.X, pady=(0, 4))

        self.lbl_nav_details = tk.Label(
            body,
            text="Expanded: 6 nodes · Edges traversed: 3 segments · Search Latency: 0.11 ms",
            font=("Consolas", 8),
            fg=C_TEXT_SECONDARY,
            bg=C_SURFACE,
        )
        self.lbl_nav_details.pack(anchor="w")

    def _build_clearance_card(self):
        """Construct the official University Entry Clearance & Dispatch card."""
        c = self.record_right

        # Card Title
        header = tk.Frame(c, bg=C_SURFACE)
        header.pack(fill=tk.X, padx=14, pady=(14, 8))

        self.lbl_doc_ref = tk.Label(header, text="REF: EC-2026-000417", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_SURFACE)
        self.lbl_doc_ref.pack(anchor="w")

        tk.Label(header, text="Campus Entry Clearance", font=("Segoe UI", 13, "bold"), fg=C_TEXT_PRIMARY, bg=C_SURFACE).pack(anchor="w", pady=(2, 0))
        tk.Label(header, text="Official University Automated Decision Dispatch", font=("Segoe UI", 8), fg=C_TEXT_SECONDARY, bg=C_SURFACE).pack(anchor="w")

        sep = tk.Frame(c, bg=C_BORDER, height=1)
        sep.pack(fill=tk.X, padx=14, pady=4)

        # Ruled details table
        details = tk.Frame(c, bg=C_SURFACE)
        details.pack(fill=tk.X, padx=14, pady=6)

        fields = [
            ("Subject Candidate", "lbl_c_candidate", "Ali Muhammad (24F-1234)"),
            ("Designated Role", "lbl_c_role", "Student"),
            ("ANN Priority", "lbl_c_priority", "URGENT"),
            ("Logic Clearance", "lbl_c_verdict", "APPROVED"),
            ("Allocated Venue", "lbl_c_venue", "Lab 1 @ 10:00 (G3)"),
            ("Computed Route", "lbl_c_route", "Parking → Science Block"),
        ]

        for i, (label_txt, attr_name, default_val) in enumerate(fields):
            row = tk.Frame(details, bg=C_SURFACE)
            row.pack(fill=tk.X, pady=4)

            tk.Label(row, text=label_txt, font=("Segoe UI", 9), fg=C_TEXT_SECONDARY, bg=C_SURFACE).pack(side=tk.LEFT)
            val_lbl = tk.Label(row, text=default_val, font=("Consolas", 9, "bold"), fg=C_TEXT_PRIMARY, bg=C_SURFACE)
            val_lbl.pack(side=tk.RIGHT)
            setattr(self, attr_name, val_lbl)

        # Reason / Notice Box (for rejections or notices)
        self.notice_box = tk.Frame(c, bg=C_SUCCESS_BG, padx=8, pady=6, highlightthickness=1, highlightbackground=C_SUCCESS)
        self.notice_box.pack(fill=tk.X, padx=14, pady=8)

        self.lbl_notice = tk.Label(
            self.notice_box,
            text="Authorization verified. Digital entry token may be issued.",
            font=("Segoe UI", 8),
            fg=C_SUCCESS,
            bg=C_SUCCESS_BG,
            wraplength=340,
            justify="left",
        )
        self.lbl_notice.pack(fill=tk.X)

        # Action Buttons
        btn_box = tk.Frame(c, bg=C_SURFACE)
        btn_box.pack(fill=tk.X, side=tk.BOTTOM, padx=14, pady=14)

        self.btn_issue_token = tk.Button(
            btn_box,
            text="Issue Digital Entry Token",
            font=("Segoe UI", 9, "bold"),
            bg=C_BRAND,
            fg=C_SURFACE,
            activebackground=C_BRAND_HOVER,
            activeforeground=C_SURFACE,
            bd=0,
            pady=7,
            cursor="hand2",
            command=self._issue_token_action,
        )
        self.btn_issue_token.pack(fill=tk.X, pady=(0, 6))

        btn_export = tk.Button(
            btn_box,
            text="Export Audit Trace (JSON)",
            font=("Segoe UI", 8),
            bg=C_SUBTLE,
            fg=C_TEXT_PRIMARY,
            activebackground=C_BORDER,
            bd=0,
            pady=5,
            cursor="hand2",
            command=self.export_audit_trace_json,
        )
        btn_export.pack(fill=tk.X)

    def _issue_token_action(self):
        """Action handler when clicking Issue Digital Token."""
        if not self.current_response:
            return
        if self.current_response.status == "APPROVED":
            messagebox.showinfo(
                "Digital Token Issued",
                f"Token successfully issued for {self.current_response.user.get('name', 'User')}!\n"
                f"Reference: {self.current_response.request_id}\n"
                f"Valid for scheduled entry."
            )
        else:
            messagebox.showwarning(
                "Token Issuance Blocked",
                "Cannot issue digital token for requests that have been rejected or faulted."
            )

    # ─── TAB 3: EXECUTION LOG & AUDIT TRACE ─────────────────────────────

    def _init_audit_log_tab(self):
        """Initialize Tab 3: Detailed Execution Log and JSON Audit Trace."""
        container = tk.Frame(self.tab_audit_log, bg=C_CANVAS)
        container.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Top timing summary bar
        top_bar = tk.Frame(container, bg=C_SURFACE, padx=12, pady=8, highlightthickness=1, highlightbackground=C_BORDER)
        top_bar.pack(fill=tk.X, pady=(0, 8))

        self.lbl_exec_total_time = tk.Label(top_bar, text="Total Pipeline Latency: 219.0 ms", font=("Consolas", 10, "bold"), fg=C_BRAND, bg=C_SURFACE)
        self.lbl_exec_total_time.pack(side=tk.LEFT)

        self.lbl_exec_hash = tk.Label(top_bar, text="Audit Hash: 0a2a39b0 (SHA-256 Provenance)", font=("Consolas", 9), fg=C_TEXT_MUTED, bg=C_SURFACE)
        self.lbl_exec_hash.pack(side=tk.RIGHT)

        # Left / Right split: Execution Steps vs Raw JSON Trace
        split_box = tk.Frame(container, bg=C_CANVAS)
        split_box.pack(fill=tk.BOTH, expand=True)

        # Left: Formatted execution step log
        log_box = tk.Frame(split_box, bg=C_SURFACE, highlightthickness=1, highlightbackground=C_BORDER)
        log_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        tk.Label(log_box, text="Sequential Pipeline Execution Log", font=("Segoe UI", 10, "bold"), fg=C_TEXT_PRIMARY, bg=C_SURFACE).pack(anchor="w", padx=10, pady=(8, 4))
        self.txt_exec_log = tk.Text(log_box, font=("Consolas", 9), bg=C_SURFACE, fg=C_TEXT_PRIMARY, bd=0, padx=8, pady=4)
        self.txt_exec_log.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        # Right: JSON Audit Trace
        json_box = tk.Frame(split_box, bg=C_SURFACE, highlightthickness=1, highlightbackground=C_BORDER)
        json_box.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))

        json_header = tk.Frame(json_box, bg=C_SURFACE)
        json_header.pack(fill=tk.X, padx=10, pady=(8, 4))
        tk.Label(json_header, text="Standardized JSON Audit Trace", font=("Segoe UI", 10, "bold"), fg=C_TEXT_PRIMARY, bg=C_SURFACE).pack(side=tk.LEFT)

        btn_copy_json = tk.Button(
            json_header,
            text="Copy JSON",
            font=("Segoe UI", 8),
            bg=C_SUBTLE,
            fg=C_TEXT_PRIMARY,
            bd=0,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self._copy_json_to_clipboard,
        )
        btn_copy_json.pack(side=tk.RIGHT)

        self.txt_audit_json = tk.Text(json_box, font=("Consolas", 8), bg=C_SUBTLE, fg=C_TEXT_PRIMARY, bd=0, padx=8, pady=4)
        self.txt_audit_json.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

    def _copy_json_to_clipboard(self):
        """Copy formatted JSON trace text to the system clipboard."""
        raw_text = self.txt_audit_json.get("1.0", tk.END).strip()
        if raw_text:
            self.clipboard_clear()
            self.clipboard_append(raw_text)
            messagebox.showinfo("Copied", "Audit Trace JSON copied to clipboard!")

    # ─── PIPELINE EXECUTION & DATA BINDING ──────────────────────────────

    def load_scenario(self, scenario_id):
        """
        Populate the intake form fields with a predefined scenario and run the pipeline.

        Args:
            scenario_id: Integer 1 to 7 corresponding to the SCENARIOS dict
        """
        if scenario_id not in SCENARIOS:
            return

        scenario = SCENARIOS[scenario_id]
        req = scenario["request"]

        # Populate form fields
        user = req.get("user", {})
        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, user.get("name", ""))

        self.ent_roll.delete(0, tk.END)
        self.ent_roll.insert(0, user.get("roll", ""))

        self.var_role.set(user.get("role", "Student"))

        req_type = req.get("request_type", "Full_Service_Request")
        self.var_req_type.set(req_type)
        self._on_req_type_changed()

        origin = req.get("origin") or "Main_Gate"
        destination = req.get("destination") or "AI_Lab"
        self.cmb_origin.set(origin)
        self.cmb_dest.set(destination)

        severity = req.get("severity", 5.0)
        self.scale_sev.set(max(0.0, min(10.0, severity)))
        self.lbl_sev_val.config(text=f"{severity:.1f} / 10" if severity >= 0 else f"{severity} (Out of range)")

        time_sens = req.get("time_sensitivity", 0.5)
        self.scale_time.set(time_sens)
        self.lbl_time_val.config(text=f"{time_sens:.2f}")

        # Execute with exact scenario request dict
        self.execute_pipeline_from_form(override_dict=req if scenario_id == 5 else None)

    def execute_pipeline_from_form(self, override_dict=None):
        """
        Collect form field values, construct request dictionary,
        and trigger the end-to-end Python AI pipeline.

        Args:
            override_dict: Optional direct request dict (e.g. for error testing)
        """
        if override_dict:
            request_dict = override_dict
        else:
            name = self.ent_name.get().strip()
            roll = self.ent_roll.get().strip()
            role = self.var_role.get()
            req_type = self.var_req_type.get()
            origin = self.cmb_origin.get()
            destination = self.cmb_dest.get()

            try:
                severity = float(self.scale_sev.get())
            except (ValueError, TypeError):
                severity = 5.0

            try:
                time_sens = float(self.scale_time.get())
            except (ValueError, TypeError):
                time_sens = 0.5

            request_dict = {
                "user": {
                    "name": name,
                    "roll": roll,
                    "role": role,
                },
                "request_type": req_type,
                "severity": severity,
                "time_sensitivity": time_sens,
                "crowd_level": 0.40,
                "distance": 0.32,
                "eligibility_flag": 1.0,
                "origin": origin,
                "destination": destination,
            }

        # Run backend pipeline
        response = run_pipeline(request_dict)
        self.current_response = response

        # Update all UI views with results
        self._render_pipeline_results(response)

    def _render_pipeline_results(self, resp):
        """
        Render the pipeline outputs across all tabs, graph, and cards.

        Args:
            resp: FinalResponse object returned by run_pipeline()
        """
        # 1. Update pipeline progress strip
        self.update_pipeline_strip(resp.pipeline_stages)

        # 2. Update Campus Navigation Graph
        if resp.search_result and resp.search_result.path:
            self.active_route_nodes = resp.search_result.path
            self.lbl_nav_alg.config(text=f"Algorithm: {resp.search_result.algorithm}")
            self.lbl_nav_cost.config(text=f"Cost: {resp.search_result.cost:.1f} units ({resp.search_result.edges} edges)")
            self.lbl_nav_time.config(text=f"Latency: {resp.search_result.exec_time:.2f} ms")
        else:
            self.active_route_nodes = []
            self.lbl_nav_alg.config(text="Algorithm: A* Search")
            self.lbl_nav_cost.config(text="Cost: —")
            self.lbl_nav_time.config(text="Latency: —")

        self._redraw_campus_graph()

        # 2b. Initialize A* Step-by-Step Walkthrough
        if resp.search_result and resp.search_result.trace:
            self._init_step_mode()
        else:
            self._disable_step_controls()

        # 3. Update ANN card
        if resp.ann_result:
            decision = resp.ann_result.mlp_class
            probs = resp.ann_result.mlp_probs
            urg_pct = probs.get("Urgent", 0.0)

            badge_color = C_WARNING if decision == "Urgent" else C_BRAND
            badge_bg = C_WARNING_BG if decision == "Urgent" else C_BRAND_TINT
            self.lbl_ann_badge.config(
                text=f"{decision.upper()} ({probs.get(decision, 0.0):.1f}%)",
                fg=badge_color,
                bg=badge_bg,
            )

            # Draw probability bar
            self._draw_ann_probability_bars(probs)
            self.lbl_ann_probs_detail.config(
                text=f"Urgent: {probs.get('Urgent', 0):.1f}% · High: {probs.get('High', 0):.1f}% · "
                     f"Normal: {probs.get('Normal', 0):.1f}% · Low: {probs.get('Low', 0):.1f}%"
            )

            if resp.preprocessing_result and resp.preprocessing_result.feature_vector:
                vec_str = [round(v, 2) for v in resp.preprocessing_result.feature_vector]
                self.lbl_feature_vec.config(text=f"7-Feature Vector: {vec_str}")
        else:
            self.lbl_ann_badge.config(text="NOT ROUTED", fg=C_TEXT_MUTED, bg=C_CANVAS)
            self.canvas_ann_bars.delete("all")
            self.lbl_ann_probs_detail.config(text="ANN stage was not routed for this request type.")
            self.lbl_feature_vec.config(text="7-Feature Vector: N/A")

        # 4. Update Logic / KB card
        if resp.logic_result:
            verdict = resp.logic_result.verdict
            is_auth = (verdict == "AUTHORIZED")
            self.lbl_logic_badge.config(
                text=verdict,
                fg=C_SUCCESS if is_auth else C_DANGER,
                bg=C_SUCCESS_BG if is_auth else C_DANGER_BG,
            )
            rules_str = ", ".join(resp.logic_result.rules_fired) if resp.logic_result.rules_fired else "None"
            self.lbl_logic_rules.config(text=f"Rules Evaluated: {rules_str}")
            self.lbl_logic_reason.config(text=resp.logic_result.reason or "Prerequisites and lab requirements verified.")
        else:
            self.lbl_logic_badge.config(text="NOT ROUTED", fg=C_TEXT_MUTED, bg=C_CANVAS)
            self.lbl_logic_rules.config(text="Rules Evaluated: —")
            self.lbl_logic_reason.config(text="Logic / KB stage was not routed for this request type.")

        # 5. Update CSP Scheduler card
        for lbl in self.csp_cells.values():
            lbl.config(text="—", bg=C_SURFACE, fg=C_TEXT_MUTED, font=("Consolas", 8))

        if resp.csp_result and resp.csp_result.solved:
            sat = sum(1 for c in resp.csp_result.constraint_results if c.get("satisfied", False))
            tot = len(resp.csp_result.constraint_results)
            self.lbl_csp_badge.config(
                text=f"{sat}/{tot} CONSTRAINTS SATISFIED",
                fg=C_SUCCESS,
                bg=C_SUCCESS_BG,
            )
            # Fill timetable
            for g_name, assign in resp.csp_result.assignment.items():
                room = assign["room"]
                slot = assign["slot"]
                cell = self.csp_cells.get((room, slot))
                if cell:
                    is_user_group = (g_name == resp.csp_result.user_group)
                    cell.config(
                        text=f"Group {g_name}",
                        bg=C_BRAND_TINT if is_user_group else C_SUBTLE,
                        fg=C_BRAND if is_user_group else C_TEXT_PRIMARY,
                        font=("Consolas", 8, "bold" if is_user_group else "normal"),
                    )

            u_grp = resp.csp_result.user_group
            u_assign = resp.csp_result.assignment.get(u_grp, {})
            u_room = u_assign.get("room", "Lab 1")
            u_slot = u_assign.get("slot", "10:00")
            self.lbl_csp_assigned.config(text=f"Assigned: Group {u_grp} → {u_room} @ {u_slot} (Precedence G4 < G3 satisfied)")
        else:
            self.lbl_csp_badge.config(text="NOT ROUTED / BYPASSED", fg=C_TEXT_MUTED, bg=C_CANVAS)
            self.lbl_csp_assigned.config(text="CSP scheduler was bypassed or not routed.")

        # 6. Update Navigation Guidance Recap
        if resp.search_result and resp.search_result.path:
            path_str = " → ".join(resp.search_result.path)
            self.lbl_nav_badge.config(text=f"OPTIMAL (Cost {resp.search_result.cost:.1f})", fg=C_BRAND, bg=C_BRAND_TINT)
            self.lbl_nav_path_text.config(text=path_str)
            self.lbl_nav_details.config(
                text=f"Expanded: {len(resp.search_result.expanded)} nodes · Traversed: {resp.search_result.edges} edges · Latency: {resp.search_result.exec_time:.2f} ms"
            )
        else:
            self.lbl_nav_badge.config(text="NOT ROUTED / BYPASSED", fg=C_TEXT_MUTED, bg=C_CANVAS)
            self.lbl_nav_path_text.config(text="No navigation route was computed.")
            self.lbl_nav_details.config(text="Navigation stage was bypassed or not routed.")

        # 7. Update Clearance Card
        user_name = resp.user.get("name", "Unknown") if resp.user else "Unknown"
        user_roll = resp.user.get("roll", "") if resp.user else ""
        user_role = resp.user.get("role", "") if resp.user else ""

        self.lbl_doc_ref.config(text=f"REF: {resp.request_id or 'EC-2026-000417'}")
        self.lbl_c_candidate.config(text=f"{user_name} ({user_roll})")
        self.lbl_c_role.config(text=user_role)

        pri_str = resp.ann_result.mlp_class if resp.ann_result else "STANDARD"
        self.lbl_c_priority.config(text=pri_str)

        status_str = resp.status
        self.lbl_c_verdict.config(
            text=status_str,
            fg=C_SUCCESS if status_str == "APPROVED" else (C_DANGER if status_str in ["REJECTED", "ERROR"] else C_TEXT_PRIMARY)
        )

        if resp.csp_result and resp.csp_result.solved:
            u_grp = resp.csp_result.user_group
            u_assign = resp.csp_result.assignment.get(u_grp, {})
            self.lbl_c_venue.config(text=f"{u_assign.get('room', '')} @ {u_assign.get('slot', '')} ({u_grp})")
        else:
            self.lbl_c_venue.config(text="None Allocated")

        if resp.search_result and resp.search_result.path:
            self.lbl_c_route.config(text=" → ".join(resp.search_result.path[1:-1]) or "Direct")
        else:
            self.lbl_c_route.config(text="N/A")

        # Notice styling
        if status_str == "APPROVED":
            self.notice_box.config(bg=C_SUCCESS_BG, highlightbackground=C_SUCCESS)
            self.lbl_notice.config(
                text="Authorization verified. Digital entry token may be issued.",
                fg=C_SUCCESS,
                bg=C_SUCCESS_BG,
            )
            self.btn_issue_token.config(state="normal")
        elif status_str == "REJECTED":
            self.notice_box.config(bg=C_DANGER_BG, highlightbackground=C_DANGER)
            reason = resp.logic_result.reason if resp.logic_result else "Failed verification"
            self.lbl_notice.config(
                text=f"REJECTED: {reason}",
                fg=C_DANGER,
                bg=C_DANGER_BG,
            )
            self.btn_issue_token.config(state="disabled")
        else:
            self.notice_box.config(bg=C_DANGER_BG, highlightbackground=C_DANGER)
            errors = "; ".join(resp.preprocessing_result.errors) if resp.preprocessing_result else "Schema validation error"
            self.lbl_notice.config(
                text=f"ERROR: {errors}",
                fg=C_DANGER,
                bg=C_DANGER_BG,
            )
            self.btn_issue_token.config(state="disabled")

        # 8. Update Execution Log & Audit Trace
        self.lbl_exec_total_time.config(text=f"Total Pipeline Latency: {resp.total_exec_time:.2f} ms")
        self.lbl_exec_hash.config(text=f"Audit Hash: {resp.get_trace_hash()} (SHA-256 Provenance)")

        # Populate execution step log
        self.txt_exec_log.delete("1.0", tk.END)
        for entry in resp.exec_log:
            stage_str = entry.get("stage", "")
            time_str = entry.get("time", "")
            detail_str = entry.get("detail", "")
            self.txt_exec_log.insert(tk.END, f"{stage_str:<12}  {time_str:<12}  {detail_str}\n")

        # Populate JSON audit trace
        self.txt_audit_json.delete("1.0", tk.END)
        trace_json = resp.get_trace_json()
        self.txt_audit_json.insert(tk.END, trace_json)

    def _draw_ann_probability_bars(self, probs):
        """Draw proportional colored bars on the ANN canvas."""
        canvas = self.canvas_ann_bars
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 10 or height <= 5:
            return

        urg = probs.get("Urgent", 0.0) / 100.0
        high = probs.get("High", 0.0) / 100.0
        norm = probs.get("Normal", 0.0) / 100.0
        low = probs.get("Low", 0.0) / 100.0

        x0 = 0
        w_urg = width * urg
        w_high = width * high
        w_norm = width * norm
        w_low = width * low

        # Urgent (Amber)
        if w_urg > 0:
            canvas.create_rectangle(x0, 0, x0 + w_urg, height, fill=C_WARNING, outline="")
            x0 += w_urg
        # High (Orange)
        if w_high > 0:
            canvas.create_rectangle(x0, 0, x0 + w_high, height, fill="#D9822B", outline="")
            x0 += w_high
        # Normal (Gray)
        if w_norm > 0:
            canvas.create_rectangle(x0, 0, x0 + w_norm, height, fill=C_TEXT_SECONDARY, outline="")
            x0 += w_norm
        # Low (Light gray)
        if w_low > 0:
            canvas.create_rectangle(x0, 0, x0 + w_low, height, fill=C_BORDER_DARK, outline="")

    def export_audit_trace_json(self):
        """Open a native file save dialog and save the complete JSON audit trace to disk."""
        if not self.current_response:
            messagebox.showwarning("Warning", "No active pipeline response to export.")
            return

        trace_json = self.current_response.get_trace_json()
        default_filename = f"audit_trace_{self.current_response.request_id or 'SC_2026'}.json"

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialfile=default_filename,
            title="Export System Audit Trace (JSON)",
        )

        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(trace_json)
                messagebox.showinfo("Export Successful", f"Audit trace exported successfully to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not write audit trace to disk:\n{str(e)}")


def main():
    """Application entry point for the desktop GUI."""
    app = SmartCampusGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
