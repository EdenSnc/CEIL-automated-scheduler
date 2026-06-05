# ui_components.py
import os
import hashlib
import logging
import re
from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QGroupBox, QLabel, QSlider, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QAbstractItemView, QFileDialog,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QMessageBox, QComboBox, QTextEdit,
    QFrame, QButtonGroup, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QColor, QPainter, QPixmap, QBrush

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = [
    "English", "French", "Spanish", "Italian",
    "German", "Swedish", "Japanese", "Chinese", "Turkish", "Russian"
]

LANGUAGE_COLORS: Dict[str, tuple] = {
    "english":  ("#C0DAFE", "#71B1FA"),
    "french":   ("#FB70BF", "#FF2395"),
    "spanish":  ("#FFB554", "#FF9B30"),
    "italian":  ("#52E084", "#16A34A"),
    "german":   ("#907C63", "#74450F"),
    "swedish":  ("#86F5DD", "#5EEAD4"),
    "japanese": ("#F9CBCB", "#FCA5A5"),
    "chinese":  ("#F97171", "#FB2424"),
    "turkish":  ("#C192F4", "#9E44FF"),
    "russian":  ("#6E6EFB", "#12339F")
}

def apply_ceil_icon(window: QWidget) -> None:
    icon_filename = "icon-ceil-removebg-preview.png"
    if os.path.exists(icon_filename):
        window.setWindowIcon(QIcon(icon_filename))

class QLogSignalHandler(QObject, logging.Handler):
    log_emitted = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)
        logging.Handler.__init__(self)

    def emit(self, record):
        try:
            msg = self.format(record)
            print(f"🔬 PROBE LOG: Emitting -> {msg}")
            self.log_emitted.emit(msg)
        except Exception as e:
            print(f"💥 PROBE LOG CRASH: {e}")


# ====================================================================
# CUSTOM UI WIDGETS
# ====================================================================

class ScheduleCardWidget(QFrame):
    def __init__(self, item_data: dict):
        super().__init__()
        self.item_data = item_data

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        lang = str(item_data.get("language", "")).strip().lower()
        self.text_color = "#0F172A" 

        if not lang or lang=="None" or lang=="none": 
            self.bg_color = "#DBDCDC"
            self.border_color = "#818181"
        elif lang in LANGUAGE_COLORS:
            color_data = LANGUAGE_COLORS[lang]
            self.bg_color = color_data[0]
            self.border_color = color_data[1]
            if len(color_data) > 2:
                self.text_color = color_data[2]
        else:
            hashed = hash(lang)
            hue = hashed % 360
            self.bg_color = QColor.fromHsl(hue, 150, 230).name()
            self.border_color = QColor.fromHsl(hue, 200, 180).name()

        self.lbl_group = QLabel(item_data.get('group', 'Unknown'))
        self.lbl_group.setStyleSheet(
            f"font-weight: 800; font-size: 13px; color: {self.text_color}; "
            "background: transparent; border: none;"
        )
        self.lbl_group.setWordWrap(True)

        self.lbl_teacher = QLabel(item_data.get('teacher', 'Unknown'))
        self.lbl_teacher.setStyleSheet(
            "font-style: italic; font-size: 11px; color: #475569; "
            "background: transparent; border: none;"
        )

        room_name = str(item_data.get('room', 'Unknown'))
        self.lbl_room = QLabel(room_name)
        self.lbl_room.setStyleSheet(
            "background-color: rgba(255,255,255,0.8); border-radius: 4px; "
            "padding: 3px 6px; font-size: 10px; color: #1E293B; font-weight: bold; border: none;"
        )

        layout.addWidget(self.lbl_group)
        layout.addWidget(self.lbl_teacher)
        layout.addWidget(self.lbl_room)

        self.setStyleSheet(
            f"ScheduleCardWidget {{ background-color: {self.bg_color}; "
            f"border: 1px solid {self.border_color}; border-radius: 6px; }}"
        )
        self.setToolTip(
            f"<b>Group:</b> {item_data.get('group')}<br>"
            f"<b>Teacher:</b> {item_data.get('teacher')}<br>"
            f"<b>Language:</b> {item_data.get('language')}<br>"
            f"<b>Room:</b> {room_name}"
        )

    def set_dimmed(self, dim: bool):
        if dim:
            self.setStyleSheet(
                "ScheduleCardWidget { background-color: #F8FAFC; border: 1px dashed #E2E8F0; border-radius: 6px; }")
            self.lbl_group.setStyleSheet(
                "font-weight: 800; font-size: 13px; color: #CBD5E1; background: transparent; border: none;")
            self.lbl_teacher.setStyleSheet(
                "font-style: italic; font-size: 11px; color: #CBD5E1; background: transparent; border: none;")
            self.lbl_room.setStyleSheet("background-color: transparent; color: transparent; border: none;")
        else:
            self.setStyleSheet(
                f"ScheduleCardWidget {{ background-color: {self.bg_color}; "
                f"border: 1px solid {self.border_color}; border-radius: 6px; }}")
            self.lbl_group.setStyleSheet(
                "font-weight: 800; font-size: 13px; color: #0F172A; background: transparent; border: none;")
            self.lbl_teacher.setStyleSheet(
                "font-style: italic; font-size: 11px; color: #475569; background: transparent; border: none;")
            self.lbl_room.setStyleSheet(
                "background-color: rgba(255,255,255,0.8); border-radius: 4px; "
                "padding: 3px 6px; font-size: 10px; color: #1E293B; font-weight: bold; border: none;")

class CellContainerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.container_layout = QVBoxLayout(self)
        self.container_layout.setContentsMargins(4, 4, 4, 4)
        self.container_layout.setSpacing(4)
        self.cards = []

    def add_card(self, item_data: dict):
        card = ScheduleCardWidget(item_data)
        self.container_layout.addWidget(card)
        self.cards.append(card)

    def apply_filter(self, query: str):
        q = query.lower()
        for card in self.cards:
            if not q:
                card.set_dimmed(False)
                continue
            match = (
                q in card.item_data.get('group', '').lower() or
                q in card.item_data.get('teacher', '').lower() or
                q in card.item_data.get('room', '').lower()
            )
            card.set_dimmed(not match)


# ====================================================================
# MAIN APPLICATION WINDOW
# ====================================================================

class SchedulingStudioMainWindow(QMainWindow):
    weight_changed = pyqtSignal(str, int)
    run_optimization_triggered = pyqtSignal(int)  # Now Passes Max Time 
    export_excel_triggered = pyqtSignal(str)
    import_excel_triggered = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CEIL Automated Timetable & Optimization Suite")
        self.setMinimumSize(1250, 800)
        apply_ceil_icon(self)

        self.full_schedule_data = []
        self.current_day = "SAT"
        self.cell_containers = []

        self.init_ui()
        self.setup_logging_bridge()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(24, 16, 24, 16)
        outer_layout.setSpacing(12)

        # ── Header ───────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        brand_icon = QLabel()
        if os.path.exists("icon-ceil-removebg-preview.png"):
            brand_icon.setPixmap(QPixmap("icon-ceil-removebg-preview.png").scaled(
                50, 50,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

        title_block = QVBoxLayout()
        main_headline = QLabel("CEIL Language Center")
        main_headline.setStyleSheet(
            "font-size: 22px; font-weight: 800; color: #1B4332; letter-spacing: -0.5px;")
        sub_headline = QLabel("Automated Timetable & Optimization Suite")
        sub_headline.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 500;")
        title_block.addWidget(main_headline)
        title_block.addWidget(sub_headline)

        header_layout.addWidget(brand_icon)
        header_layout.addLayout(title_block)
        header_layout.addStretch()

        actions_group = QHBoxLayout()
        self.btn_import = QPushButton("Import Spreadsheet")
        self.btn_import.setStyleSheet(
            "background-color: #FFFFFF; color: #1B4332; border: 1px solid #1B4332; "
            "padding: 6px 12px; font-weight: 600;")
        self.btn_export = QPushButton("Export Timetable")
        self.btn_export.setStyleSheet(
            "background-color: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; "
            "padding: 6px 12px; font-weight: 600;")

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #10B981; font-size: 14px; margin-right: 2px;")
        self.status_text = QLabel("Engine Ready")
        self.status_text.setStyleSheet(
            "font-weight: 600; color: #334155; margin-right: 16px;")

        actions_group.addWidget(self.status_dot)
        actions_group.addWidget(self.status_text)
        actions_group.addWidget(self.btn_import)
        actions_group.addWidget(self.btn_export)
        header_layout.addLayout(actions_group)
        outer_layout.addLayout(header_layout)

        self.tabs = QTabWidget()
        outer_layout.addWidget(self.tabs)

        # ── DASHBOARD TAB ─────────────────────────────────────────────
        dashboard_tab = QWidget()
        dash_layout = QVBoxLayout()
        dash_layout.setSpacing(4)
        dash_layout.setContentsMargins(0, 0, 0, 0)
        dashboard_tab.setLayout(dash_layout)

        self.weights_box = QGroupBox("Optimization Directives & Penalty Matrix Coefficients")
        weights_main_layout = QVBoxLayout(self.weights_box)

        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        self.btn_reset_weights = QPushButton("⟲ Reset Defaults")
        self.btn_reset_weights.setStyleSheet(
            "background-color: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; padding: 4px 10px;"
        )
        reset_layout.addWidget(self.btn_reset_weights)
        weights_main_layout.addLayout(reset_layout)

        # --- Symmetrical Grid Layout ---
        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(12)
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)

        self.sliders = {}
        parameters = [
            ("W_PREFERENCE", "Teacher Preferences", "Reward/Penalty multiplier for shift availability."),
            ("W_GAP", "Avoid Trapped Gaps", "Penalizes unallocated blocks between active sessions."),
            ("W_LOAD_BALANCE", "Normalize Workload", "Balances assignments to avoid heavy vs empty days."),
            ("W_FAIRNESS", "Teacher Fairness", "Prevents dumping all bad shifts onto a single teacher."),
            ("W_ROOM_CHANGE", "Room Continuity", "Penalizes back-to-back classes in different rooms."),
            ("W_COGNITIVE", "Cognitive Whiplash", "Penalizes jumping between extreme levels back-to-back."),
        ]

        for idx, (key, label, desc) in enumerate(parameters):
            cell_widget = QWidget()
            cell_widget.setMinimumHeight(60)

            cell_layout = QVBoxLayout(cell_widget)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(1)

            lbl_title = QLabel(
                f"**{label}**: "
                f"{desc}")
            lbl_title.setWordWrap(True)
            from PyQt6.QtWidgets import QSizePolicy
            lbl_title.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.MinimumExpanding,
            )

            slider_row = QHBoxLayout()
            sld = QSlider(Qt.Orientation.Horizontal)
            sld.setRange(0, 100)
            sld.setValue(10)
            sld.setMinimumWidth(120)

            lbl_val = QLabel("10")
            lbl_val.setStyleSheet("font-weight: bold; color: #1B4332; min-width: 28px;")
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            sld.valueChanged.connect(
                lambda v, k=key, lv=lbl_val: [lv.setText(str(v)),
                                              self.weight_changed.emit(k, v)]
            )
            slider_row.addWidget(sld, 1)
            slider_row.addWidget(lbl_val)

            cell_layout.addWidget(lbl_title)
            cell_layout.addLayout(slider_row)

            row = idx // 2
            col = idx % 2
            grid_layout.addWidget(cell_widget, row, col)

            self.sliders[key] = sld

        grid_container = QWidget()
        grid_container.setLayout(grid_layout)
        grid_container.setStyleSheet("background: transparent;")

        scroll_area = QScrollArea()
        scroll_area.setWidget(grid_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        weights_main_layout.addWidget(scroll_area)
        dash_layout.addWidget(self.weights_box)

        # ── SOLVER CONTROL CENTER ─────────────────────────────────────────────
        solver_box = QGroupBox("Solver Control Center")
        solver_layout = QVBoxLayout(solver_box)
        solver_layout.setContentsMargins(16, 10, 16, 10)

        # Execution Time Slider (Independent of Weights)
        time_layout = QHBoxLayout()
        lbl_time_title = QLabel("**Solver Max Execution Time (Seconds)**: Limits how long the CP-SAT engine searches for a valid schedule.")
        lbl_time_title.setWordWrap(True)
        
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setRange(30, 300)
        self.time_slider.setValue(60)
        self.time_slider.setMinimumWidth(120)

        self.time_val_lbl = QLabel("60")
        self.time_val_lbl.setStyleSheet("font-weight: bold; color: #1B4332; min-width: 28px;")
        self.time_val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.time_slider.valueChanged.connect(lambda v: self.time_val_lbl.setText(str(v)))

        time_layout.addWidget(lbl_time_title)
        time_layout.addWidget(self.time_slider, 1)
        time_layout.addWidget(self.time_val_lbl)

        self.btn_solve = QPushButton("Compile Optimized Schedule")
        self.btn_solve.setObjectName("SolverButton")
        self.btn_solve.setMinimumWidth(300)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_solve)
        btn_layout.addStretch()

        solver_layout.addLayout(time_layout)
        solver_layout.addLayout(btn_layout)

        dash_layout.addStretch()
        dash_layout.addWidget(solver_box)
        self.tabs.addTab(dashboard_tab, "Control Dashboard")

        # ── Entity-management tabs ────────────────────────────────────
        self.teacher_tab = TeacherManagementTab()
        self.group_tab = GroupManagementTab()
        self.room_tab = RoomManagementTab()

        self.tabs.addTab(self.teacher_tab, "Teacher Profiles")
        self.tabs.addTab(self.group_tab, "Student Groups")
        self.tabs.addTab(self.room_tab, "Classrooms")

        # ── TIMETABLE MATRIX VIEW ─────────────────────────────────────
        schedule_tab = QWidget()
        sched_layout = QVBoxLayout(schedule_tab)

        toolbar_layout = QHBoxLayout()
        self.day_buttons = []
        self.btn_group = QButtonGroup(self)

        for day in ["SAT", "SUN", "MON", "TUE", "WED", "THU"]:
            btn = QPushButton(day)
            btn.setCheckable(True)
            if day == "SAT":
                btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9; color: #64748B; border: none;
                    padding: 8px 16px; font-weight: 800; border-radius: 6px;
                }
                QPushButton:checked { background-color: #1B4332; color: white; }
                QPushButton:hover:!checked { background-color: #E2E8F0; }
            """)
            btn.clicked.connect(lambda checked, d=day: self.switch_day(d))
            self.btn_group.addButton(btn)
            self.day_buttons.append(btn)
            toolbar_layout.addWidget(btn)

        toolbar_layout.addStretch()

        self.search_filter = QLineEdit()
        self.search_filter.setPlaceholderText("🔍 Quick Filter: Teacher, Group, or Room...")
        self.search_filter.setMinimumWidth(300)
        self.search_filter.setStyleSheet(
            "padding: 8px 12px; border: 1px solid #CBD5E1; border-radius: 6px; "
            "background-color: #F8FAFC; color: #0F172A;")
        self.search_filter.textChanged.connect(self.apply_schedule_filter)
        toolbar_layout.addWidget(self.search_filter)

        sched_layout.addLayout(toolbar_layout)

        self.schedule_table = QTableWidget(0, 0)
        self.schedule_table.setShowGrid(False)
        self.schedule_table.setAlternatingRowColors(True)
        self.schedule_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.schedule_table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #F1F5F9; color: #475569;
                font-weight: bold; border: none; padding: 4px;
            }
        """)
        sched_layout.addWidget(self.schedule_table)
        self.tabs.addTab(schedule_tab, "Timetable View")

        # ── Debug / console panel ─────────────────────────────────────
        self.debug_box = QGroupBox("System Trace Logs")
        self.debug_box.setCheckable(True)
        self.debug_box.setChecked(False)

        self.debug_layout = QVBoxLayout(self.debug_box)
        self.debug_layout.setContentsMargins(8, 8, 8, 8)

        self.debug_console = QTextEdit()
        self.debug_console.setObjectName("DebugLogConsole")
        self.debug_console.setReadOnly(True)
        self.debug_console.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.debug_console.setVisible(False)
        self.debug_layout.addWidget(self.debug_console)

        self.debug_box.setFixedHeight(32)

        def _toggle_debug(open_state: bool):
            self.debug_console.setVisible(open_state)
            self.debug_box.setFixedHeight(240 if open_state else 32)

        self.debug_box.toggled.connect(_toggle_debug)

        outer_layout.addWidget(self.debug_box)
        self.statusBar().showMessage("Platform framework targets initialized.")

        # Passes value dynamically
        self.btn_solve.clicked.connect(lambda: self.run_optimization_triggered.emit(self.time_slider.value())) 
        self.btn_export.clicked.connect(self.trigger_excel_egress)
        self.btn_import.clicked.connect(self.trigger_excel_ingress)

    def setup_logging_bridge(self):
        self._log_handler = QLogSignalHandler()
        self._log_handler.log_emitted.connect(self.append_log_message)
        logging.getLogger().addHandler(self._log_handler)
        logging.getLogger().setLevel(logging.INFO)

    def append_log_message(self, msg: str):
        self.debug_console.append(msg)
        self.debug_console.verticalScrollBar().setValue(
            self.debug_console.verticalScrollBar().maximum())

    def switch_day(self, day: str):
        self.current_day = day
        self.render_day_view()

    def display_schedule(self, schedule_items: List[Dict[str, Any]]) -> None:
        self.full_schedule_data = schedule_items
        self.render_day_view()

    def render_day_view(self):
        self.schedule_table.setUpdatesEnabled(False)
        self.schedule_table.clear()
        self.cell_containers.clear()

        if not self.full_schedule_data:
            self.schedule_table.setRowCount(0)
            self.schedule_table.setColumnCount(0)
            self.schedule_table.setUpdatesEnabled(True)
            return

        day_items = [
            item for item in self.full_schedule_data
            if item.get("day", "").upper() == self.current_day.upper()
        ]

        slots = sorted(list(set(item.get("slot", "") for item in self.full_schedule_data)))
        if not slots:
            slots = ["08:30-10:30", "10:30-12:30", "13:30-15:30", "15:30-17:30", "17:30-19:30"]
        rooms = sorted(list(set(item.get("room", "") for item in self.full_schedule_data)))

        self.schedule_table.setRowCount(len(slots))
        self.schedule_table.setColumnCount(len(rooms))
        self.schedule_table.setVerticalHeaderLabels(slots)
        self.schedule_table.setHorizontalHeaderLabels(rooms)

        grid = {s: {r: [] for r in rooms} for s in slots}
        for item in day_items:
            s = item.get("slot")
            r = item.get("room")
            if s in grid and r in grid[s]:
                grid[s][r].append(item)

        for row_idx, s in enumerate(slots):
            for col_idx, r in enumerate(rooms):
                items = grid[s][r]
                if items:
                    container = CellContainerWidget()
                    for item in items:
                        container.add_card(item)
                    self.schedule_table.setCellWidget(row_idx, col_idx, container)
                    self.cell_containers.append(container)
                else:
                    empty_lbl = QLabel("---")
                    empty_lbl.setStyleSheet("color: #CBD5E1; text-align: center;")
                    empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.schedule_table.setCellWidget(row_idx, col_idx, empty_lbl)

        self.schedule_table.resizeRowsToContents()
        self.schedule_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive)
        self.schedule_table.horizontalHeader().setDefaultSectionSize(160)
        self.apply_schedule_filter(self.search_filter.text())
        self.schedule_table.setUpdatesEnabled(True)

    def apply_schedule_filter(self, text: str):
        for container in self.cell_containers:
            container.apply_filter(text)

    def set_weights_ui_values(self, weights: Dict[str, int]) -> None:
        for key, value in weights.items():
            if key in self.sliders:
                self.sliders[key].setValue(value)

    def trigger_excel_egress(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Timetable", "", "Excel Files (*.xlsx)")
        if file_path:
            self.export_excel_triggered.emit(file_path)

    def trigger_excel_ingress(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Spreadsheet", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.import_excel_triggered.emit(file_path)

# ... (The rest of the BaseEntityManagementTab, RoomManagementTab, TeacherManagementTab, GroupManagementTab, and TeacherPreferencesDialog components remain functionally unmodified and perfectly intact) ...

class BaseEntityManagementTab(QWidget):
    create_requested = pyqtSignal(dict)
    update_requested = pyqtSignal(int, dict)
    delete_requested = pyqtSignal(int)

    def __init__(self, entity_name: str, display_columns: List[str], data_keys: List[str]):
        super().__init__()
        self.entity_name = entity_name
        self.display_columns = display_columns
        self.data_keys = data_keys
        self.current_data = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header_layout = QHBoxLayout()
        title = QLabel(f"Manage {self.entity_name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")

        singular = (self.entity_name[:-1]
                    if self.entity_name.endswith('s')
                    else self.entity_name)
        btn_add = QPushButton(f"➕ Add New {singular}")
        btn_add.clicked.connect(self.show_add_dialog)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_add)
        layout.addLayout(header_layout)

        self.table = QTableWidget(0, len(self.display_columns) + 1)
        self.table.setHorizontalHeaderLabels(self.display_columns + ["Actions"])

        header = self.table.horizontalHeader()
        header.setDefaultSectionSize(120)
        n = len(self.display_columns)
        for i in range(n - 1):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        if n > 0:
            header.setSectionResizeMode(n - 1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(n, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setWordWrap(True)
        layout.addWidget(self.table)

    def render_data(self, data: List[Dict[str, Any]]):
        self.current_data = data
        self.table.setRowCount(0)
        for row_idx, item in enumerate(data):
            self.table.insertRow(row_idx)
            for col_idx, key in enumerate(self.data_keys):
                val = item.get(key, "")
                if isinstance(val, bool):
                    val = "Yes" if val else "No"
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))
            self.add_action_buttons(row_idx)
        self.table.resizeRowsToContents()

    def add_action_buttons(self, row_idx: int):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        btn_edit = QPushButton("Edit")
        btn_edit.setStyleSheet("background-color: #F1F5F9; color: #475569;")
        btn_edit.clicked.connect(lambda _, r=row_idx: self.show_edit_dialog(r))

        btn_delete = QPushButton("Delete")
        btn_delete.setObjectName("DangerButton")
        btn_delete.clicked.connect(lambda _, r=row_idx: self.delete_requested.emit(r))

        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        layout.addStretch()
        self.table.setCellWidget(row_idx, len(self.display_columns), widget)

class RoomManagementTab(BaseEntityManagementTab):
    def __init__(self):
        super().__init__(
            "Classrooms",
            ["Room ID", "Room Name", "Capacity"],
            ["id", "name", "capacity"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

    def show_add_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Classroom")
        layout = QFormLayout(dialog)

        name_in = QLineEdit()
        cap_in = QSpinBox()
        cap_in.setRange(5, 100)
        cap_in.setValue(25)
        special_cb = QComboBox()
        special_cb.addItems(["False", "True"])

        layout.addRow("Room Name:", name_in)
        layout.addRow("Seating Capacity:", cap_in)
        layout.addRow("Is IELTS Tracking Enabled?:", special_cb)

        btn_save = QPushButton("Save Room")
        btn_save.clicked.connect(lambda: [
            self.create_requested.emit({
                "name": name_in.text(),
                "capacity": cap_in.value(),
                "is_special": special_cb.currentText() == "True"
            }),
            dialog.accept()
        ])
        layout.addRow(btn_save)
        dialog.exec()

    def show_edit_dialog(self, row_idx: int):
        room = self.current_data[row_idx]
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit {room.get('name')}")
        layout = QFormLayout(dialog)

        name_in = QLineEdit(room.get("name", ""))
        cap_in = QSpinBox()
        cap_in.setRange(5, 100)
        cap_in.setValue(room.get("capacity", 25))
        special_cb = QComboBox()
        special_cb.addItems(["False", "True"])
        special_cb.setCurrentText("True" if room.get("is_special") else "False")

        layout.addRow("Room Name:", name_in)
        layout.addRow("Seating Capacity:", cap_in)
        layout.addRow("Is IELTS Tracking Enabled?:", special_cb)

        btn_save = QPushButton("Update Room")
        btn_save.clicked.connect(lambda: [
            self.update_requested.emit(row_idx, {
                "name": name_in.text(),
                "capacity": cap_in.value(),
                "is_special": special_cb.currentText() == "True"
            }),
            dialog.accept()
        ])
        layout.addRow(btn_save)
        dialog.exec()

class TeacherManagementTab(BaseEntityManagementTab):
    preferences_requested = pyqtSignal(int, str, dict)

    def __init__(self):
        super().__init__(
            "Teaching Staff",
            ["ID", "Full Name", "Weekly Hours Cap", "Skill Matrix"],
            ["id", "name", "max_hours", "skills"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

    def add_action_buttons(self, row_idx: int):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        btn_pref = QPushButton("Availability")
        btn_pref.setStyleSheet("background-color: #E0F2FE; color: #0284C7;")
        btn_pref.clicked.connect(lambda _, r=row_idx: self.emit_preferences(r))

        btn_edit = QPushButton("Edit")
        btn_edit.setStyleSheet("background-color: #F1F5F9; color: #475569;")
        btn_edit.clicked.connect(lambda _, r=row_idx: self.show_edit_dialog(r))

        btn_delete = QPushButton("Delete")
        btn_delete.setObjectName("DangerButton")
        btn_delete.clicked.connect(lambda _, r=row_idx: self.delete_requested.emit(r))

        layout.addWidget(btn_pref)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        self.table.setCellWidget(row_idx, len(self.display_columns), widget)

    def emit_preferences(self, row_idx: int):
        teacher = self.current_data[row_idx]
        self.preferences_requested.emit(
            row_idx, teacher.get("name", "Unknown"), teacher.get("preferences", {}))

    def show_add_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Register New Teacher")
        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        hours_input = QSpinBox()
        hours_input.setRange(2, 40)
        hours_input.setValue(20)
        skills_input = QLineEdit()

        layout.addRow("Full Name:", name_input)
        layout.addRow("Max Hours/Week:", hours_input)
        layout.addRow("Skills (comma separated):", skills_input)

        btn_save = QPushButton("Save Record")
        btn_save.clicked.connect(lambda: [
            self.create_requested.emit({
                "name": name_input.text(),
                "max_hours": hours_input.value(),
                "skills": skills_input.text()
            }),
            dialog.accept()
        ])
        layout.addRow(btn_save)
        dialog.exec()

    def show_edit_dialog(self, row_idx: int):
        teacher = self.current_data[row_idx]
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit {teacher.get('name')}")
        layout = QFormLayout(dialog)

        name_input = QLineEdit(teacher.get("name", ""))
        hours_input = QSpinBox()
        hours_input.setRange(2, 40)
        hours_input.setValue(teacher.get("max_hours", 20))
        skills_input = QLineEdit(teacher.get("skills", ""))

        layout.addRow("Full Name:", name_input)
        layout.addRow("Max Hours/Week:", hours_input)
        layout.addRow("Skills:", skills_input)

        btn_save = QPushButton("Update Record")
        btn_save.clicked.connect(lambda: [
            self.update_requested.emit(row_idx, {
                "name": name_input.text(),
                "max_hours": hours_input.value(),
                "skills": skills_input.text()
            }),
            dialog.accept()
        ])
        layout.addRow(btn_save)
        dialog.exec()

class GroupManagementTab(BaseEntityManagementTab):
    makeup_requested = pyqtSignal(int)  # <-- Add this signal
    def __init__(self):
        super().__init__(
            "Student Groups",
            ["ID", "Cohort Alias", "Language", "CEFR Level",
             "Sessions/Wk", "Track Modifiers", "Assigned Teacher"],
            ["id", "name", "language", "level",
             "sessions_per_week", "modifiers", "teacher_name"])
        self.teacher_map: Dict[str, str] = {}

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

    def add_action_buttons(self, row_idx: int):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Scoped exclusively here so it never bleeds into other dashboard panels again
        btn_makeup = QPushButton("Manage Makeup")
        btn_makeup.setStyleSheet("background-color: #EFF6FF; color: #2563EB; font-weight: bold; border: 1px solid #BFDBFE;")
        btn_makeup.clicked.connect(lambda _, r=row_idx: self.makeup_requested.emit(r))

        btn_edit = QPushButton("Edit")
        btn_edit.setStyleSheet("background-color: #F1F5F9; color: #475569;")
        btn_edit.clicked.connect(lambda _, r=row_idx: self.show_edit_dialog(r))

        btn_delete = QPushButton("Delete")
        btn_delete.setObjectName("DangerButton")
        btn_delete.clicked.connect(lambda _, r=row_idx: self.delete_requested.emit(r))

        layout.addWidget(btn_makeup)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        self.table.setCellWidget(row_idx, len(self.display_columns), widget)

    def set_teacher_map(self, t_map: Dict[str, str]):
        self.teacher_map = t_map

    def render_data(self, data: List[Dict[str, Any]]):
        enriched_data = []
        for item in data:
            row = dict(item)
            mods = []
            if row.get("is_evening"):  mods.append("Evening")
            if row.get("is_si"):       mods.append("Semi-Intensive")
            if row.get("is_ielts"):    mods.append("IELTS")
            row["modifiers"] = " | ".join(mods) if mods else "Standard"
            row["teacher_name"] = self.teacher_map.get(
                row.get("teacher_id", ""), row.get("teacher_id", "Unassigned"))
            enriched_data.append(row)

        self.current_data = enriched_data
        self.table.setRowCount(0)
        
        for row_idx, item in enumerate(enriched_data):
            self.table.insertRow(row_idx)
            
# Clean up the incoming string (strip spaces and uppercase it)
            level_str = str(item.get("level", "")).strip().upper()
            bg_color = QColor("#FFFFFF") # Default background

            # Define strict standard CEFR levels allowed to have background highlights
            CEFR_PATTERN = re.compile(r"^[ABC][12].*")
            # Check if it starts with a valid level
            if CEFR_PATTERN.match(level_str):
                # We slice the first char because [ABC] is guaranteed by the regex
                group_prefix = level_str[0]
                
                if group_prefix == "A":
                    bg_color = QColor("#A7FCB4") # Green
                elif group_prefix == "B":
                    bg_color = QColor("#A4C5FD") # Blue
                elif group_prefix == "C":
                    bg_color = QColor("#D1A9FF") # Purple

            cell_brush = QBrush(bg_color)

            for col_idx, key in enumerate(self.data_keys):
                val = item.get(key, "")
                if isinstance(val, bool):
                    val = "Yes" if val else "No"

                table_item = QTableWidgetItem(str(val))
                table_item.setBackground(cell_brush)
                self.table.setItem(row_idx, col_idx, table_item)
            self.add_action_buttons(row_idx)
        self.table.resizeRowsToContents()

    @staticmethod
    def _make_lang_combo(current_value: str = "") -> QComboBox:
        cb = QComboBox()
        cb.addItems(SUPPORTED_LANGUAGES)
        for lang in SUPPORTED_LANGUAGES:
            if lang.lower() == current_value.strip().lower():
                cb.setCurrentText(lang)
                break
        return cb

    def show_add_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Register Student Group")
        layout = QFormLayout(dialog)

        name_in    = QLineEdit()
        lang_cb    = self._make_lang_combo()
        level_in   = QLineEdit()

        sess_in = QSpinBox()
        sess_in.setRange(1, 10)
        sess_in.setValue(2)

        cefr_in = QSpinBox()
        cefr_in.setRange(1, 6)
        cefr_in.setValue(1)

        evening_cb = QComboBox(); evening_cb.addItems(["False", "True"])
        si_cb      = QComboBox(); si_cb.addItems(["False", "True"])
        ielts_cb   = QComboBox(); ielts_cb.addItems(["False", "True"])

        teacher_cb = QComboBox()
        for t_id, t_name in self.teacher_map.items():
            teacher_cb.addItem(f"{t_name} ({t_id})", t_id)

        layout.addRow("Group Designation:",           name_in)
        layout.addRow("Language:",                     lang_cb)
        layout.addRow("CEFR String (e.g. A1.1):",     level_in)
        layout.addRow("CEFR Numeric Level (1-6):",    cefr_in)
        layout.addRow("Sessions Per Week:",            sess_in)
        layout.addRow("Evening Track (17:30 only):",  evening_cb)
        layout.addRow("Semi-Intensive (4 Days/Wk):",  si_cb)
        layout.addRow("IELTS Track (Teacher's Room):", ielts_cb)
        layout.addRow("Assigned Teacher:",             teacher_cb)

        btn_save = QPushButton("Save Group")
        btn_save.clicked.connect(lambda: [
            self.create_requested.emit({
                "name":             name_in.text(),
                "language":         lang_cb.currentText(),
                "level":            level_in.text(),
                "cefr_numeric":     cefr_in.value(),
                "sessions_per_week": sess_in.value(),
                "is_evening":       evening_cb.currentText() == "True",
                "is_si":            si_cb.currentText() == "True",
                "is_ielts":         ielts_cb.currentText() == "True",
                "teacher_id":       teacher_cb.currentData()
            }),
            dialog.accept()
        ])
        layout.addRow(btn_save)
        dialog.exec()

    def show_edit_dialog(self, row_idx: int):
        group = self.current_data[row_idx]
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Group {group.get('name')}")
        layout = QFormLayout(dialog)

        name_in  = QLineEdit(group.get("name", ""))
        lang_cb  = self._make_lang_combo(group.get("language", ""))
        level_in = QLineEdit(group.get("level", ""))

        sess_in = QSpinBox()
        sess_in.setRange(1, 10)
        sess_in.setValue(group.get("sessions_per_week", 2))

        cefr_in = QSpinBox()
        cefr_in.setRange(1, 6)
        cefr_in.setValue(group.get("cefr_numeric", 1))

        evening_cb = QComboBox(); evening_cb.addItems(["False", "True"])
        evening_cb.setCurrentText("True" if group.get("is_evening") else "False")

        si_cb = QComboBox(); si_cb.addItems(["False", "True"])
        si_cb.setCurrentText("True" if group.get("is_si") else "False")

        ielts_cb = QComboBox(); ielts_cb.addItems(["False", "True"])
        ielts_cb.setCurrentText("True" if group.get("is_ielts") else "False")

        teacher_cb = QComboBox()
        current_tid = group.get("teacher_id")
        for i, (t_id, t_name) in enumerate(self.teacher_map.items()):
            teacher_cb.addItem(f"{t_name} ({t_id})", t_id)
            if t_id == current_tid:
                teacher_cb.setCurrentIndex(i)

        layout.addRow("Group Designation:",           name_in)
        layout.addRow("Language:",                     lang_cb)
        layout.addRow("CEFR String (e.g. A1.1):",     level_in)
        layout.addRow("CEFR Numeric Level (1-6):",    cefr_in)
        layout.addRow("Sessions Per Week:",            sess_in)
        layout.addRow("Evening Track (17:30 only):",  evening_cb)
        layout.addRow("Semi-Intensive (4 Days/Wk):",  si_cb)
        layout.addRow("IELTS Track (Teacher's Room):", ielts_cb)
        layout.addRow("Assigned Teacher:",             teacher_cb)

        btn_save = QPushButton("Update Group")
        btn_save.clicked.connect(lambda: [
            self.update_requested.emit(row_idx, {
                "name":             name_in.text(),
                "language":         lang_cb.currentText(),
                "level":            level_in.text(),
                "cefr_numeric":     cefr_in.value(),
                "sessions_per_week": sess_in.value(),
                "is_evening":       evening_cb.currentText() == "True",
                "is_si":            si_cb.currentText() == "True",
                "is_ielts":         ielts_cb.currentText() == "True",
                "teacher_id":       teacher_cb.currentData()
            }),
            dialog.accept()
        ])
        layout.addRow(btn_save)
        dialog.exec()

class TeacherPreferencesDialog(QDialog):
    def __init__(self, teacher_name: str, current_prefs: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Availability Matrix: {teacher_name}")
        self.setMinimumSize(850, 550)
        self.current_prefs = current_prefs
        self.days = ["SAT", "SUN", "MON", "TUE", "WED", "THU"]
        self.slots = ["08:30-10:30", "10:30-12:30", "13:30-15:30",
                      "15:30-17:30", "17:30-19:30"]
        self.combos = {}
        self.init_ui()

    def init_ui(self):
        # 1. Base Dialog QSS (Encapsulated Styling)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
            }
            QWidget#MainCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
            QLabel#DayHeader {
                font-size: 12px;
                font-weight: bold;
                color: #1E293B;
                padding: 12px 8px;
            }
            QLabel#TimeHeader {
                font-size: 12px;
                font-weight: bold;
                color: #64748B;
                padding: 8px 16px 8px 8px;
            }
            QPushButton#SaveBtn {
                background-color: #0F172A;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#SaveBtn:hover {
                background-color: #1E293B;
            }
            QPushButton#CancelBtn {
                background-color: #FFFFFF;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#CancelBtn:hover {
                background-color: #F1F5F9;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 2. Modern Legend (Pill Badges)
        legend_layout = QHBoxLayout()
        legend_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        legend_layout.setSpacing(12)

        def create_legend_pill(text: str, bg: str, fg: str, border: str = None) -> QLabel:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bnd_css = f"border: 1px solid {border};" if border else "border: none;"
            lbl.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg};
                    color: {fg};
                    font-weight: bold;
                    font-size: 11.5px;
                    border-radius: 12px;
                    padding: 6px 16px;
                    {bnd_css}
                }}
            """)
            return lbl

        legend_layout.addWidget(create_legend_pill("Preferred", "#DCFCE7", "#15803D", "#86EFAC"))
        legend_layout.addWidget(create_legend_pill("Neutral", "#FFFFFF", "#475569", "#E2E8F0"))
        legend_layout.addWidget(create_legend_pill("Dislike", "#FEF3C7", "#B45309", "#FDE68A"))
        legend_layout.addWidget(create_legend_pill("Unavailable", "#FEE2E2", "#B91C1C", "#FECACA"))
        
        layout.addLayout(legend_layout)

        # 3. Main Central Card Container
        card_widget = QWidget()
        card_widget.setObjectName("MainCard")
        card_layout = QVBoxLayout(card_widget)
        card_layout.setContentsMargins(20, 20, 20, 20)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Headers
        for col, day in enumerate(self.days):
            lbl = QLabel(day)
            lbl.setObjectName("DayHeader")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(lbl, 0, col + 1)

        for row, slot in enumerate(self.slots):
            lbl = QLabel(slot)
            lbl.setObjectName("TimeHeader")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(lbl, row + 1, 0)

            # Combobox Matrix
            for col, day in enumerate(self.days):
                cb = QComboBox()
                cb.addItems(["Neutral", "Preferred", "Dislike", "Unavailable"])

                # Data mapping retrieval
                if day in self.current_prefs and isinstance(self.current_prefs[day], dict):
                    val = self.current_prefs[day].get(str(row), "neutral")
                else:
                    val = self.current_prefs.get(f"{day}_{row}", "neutral")

                cb.setCurrentText(val.capitalize())

                # Hook dynamic styling
                cb.currentTextChanged.connect(lambda _, c=cb: self.update_combo_style(c))
                self.update_combo_style(cb)  # Apply initial state style

                self.combos[f"{day}_{row}"] = cb
                grid.addWidget(cb, row + 1, col + 1)

        card_layout.addLayout(grid)
        layout.addWidget(card_widget)
        layout.addStretch()

        # 4. Action Buttons Footer
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("CancelBtn")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save Availability")
        btn_save.setObjectName("SaveBtn")
        btn_save.clicked.connect(self.accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def update_combo_style(self, combo: QComboBox):
        """Dynamically builds and applies a custom stylesheet to match the selected tier"""
        val = combo.currentText()
        if val == "Preferred":
            bg, fg, bnd = "#DCFCE7", "#15803D", "#86EFAC"
        elif val == "Dislike":
            bg, fg, bnd = "#FEF3C7", "#B45309", "#FDE68A"
        elif val == "Unavailable":
            bg, fg, bnd = "#FEE2E2", "#B91C1C", "#FECACA"
        else:  # Neutral
            bg, fg, bnd = "#FFFFFF", "#475569", "#CBD5E1"

        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {bnd};
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: bold;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 0px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0px;
                height: 0px;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {fg};
                margin-top: 2px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #FFFFFF;
                color: #0F172A;
                selection-background-color: #F8FAFC;
                selection-color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px;
            }}
        """)

    def get_preferences(self) -> dict:
        prefs = {}
        for day in self.days:
            prefs[day] = {}
            for row in range(len(self.slots)):
                val = self.combos[f"{day}_{row}"].currentText().lower()
                prefs[day][str(row)] = val
        return prefs

class GroupMakeupManagerDialog(QDialog):
    def __init__(self, group_id: str, group_name: str, teacher_id: str, teacher_name: str, rooms: list, current_schedule: list, locked_sessions: list, teacher_prefs: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Manage Makeup Schedule — {group_name}")
        self.setMinimumSize(1150, 650)
        
        self.group_id = group_id
        self.group_name = group_name
        self.teacher_id = teacher_id
        self.teacher_name = teacher_name
        self.rooms = rooms
        
        import copy
        self.current_schedule = copy.deepcopy(current_schedule)
        self.locked_sessions = copy.deepcopy(locked_sessions)
        self.teacher_prefs = teacher_prefs or {}
        
        self.pending_additions = []
        self.pending_deletions = []
        
        self.days = ["SAT", "SUN", "MON", "TUE", "WED", "THU"]
        self.slots = ["08:30-10:30", "10:30-12:30", "13:30-15:30", "15:30-17:30", "17:30-19:30"]
        
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #F8FAFC; }
            QWidget#SidebarPane { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
            QWidget#MainCard { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; }
            QLabel#HeaderTitle { font-size: 16px; font-weight: 800; color: #0F172A; }
            QLabel#SectionTitle { font-size: 14px; font-weight: 700; color: #334155; }
            QLabel#DayHeader { font-size: 11px; font-weight: bold; color: #1E293B; padding: 4px; }
            QLabel#TimeHeader { font-size: 10px; font-weight: bold; color: #64748B; padding-right: 4px; }
            QTableWidget { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; }
            QHeaderView::section { background-color: #F1F5F9; font-weight: bold; color: #475569; border: none; padding: 6px; font-size: 11px; }
            QPushButton#SaveBtn { background-color: #2563EB; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold; font-size: 13px; }
            QPushButton#SaveBtn:hover { background-color: #1D4ED8; }
            QPushButton#CancelBtn { background-color: #FFFFFF; color: #475569; border: 1px solid #CBD5E1; border-radius: 6px; padding: 10px 24px; font-weight: bold; font-size: 13px; }
            QPushButton#CancelBtn:hover { background-color: #F1F5F9; }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── LEFT SIDEBAR: ACTIVE LEDGER ───
        sidebar = QWidget()
        sidebar.setObjectName("SidebarPane")
        sidebar.setFixedWidth(360)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(12)

        lbl_ledger_title = QLabel("Active Makeup Sessions")
        lbl_ledger_title.setObjectName("SectionTitle")
        sidebar_layout.addWidget(lbl_ledger_title)

        self.ledger_table = QTableWidget(0, 3)
        self.ledger_table.setHorizontalHeaderLabels(["Room", "Time Coordinate", "Action"])
        self.ledger_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ledger_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ledger_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.ledger_table.setShowGrid(False)
        self.ledger_table.setAlternatingRowColors(True)
        sidebar_layout.addWidget(self.ledger_table)
        
        main_layout.addWidget(sidebar)

        # ─── RIGHT WORKSPACE: HEATMAP FINDER ───
        workspace = QWidget()
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(24, 20, 24, 20)
        workspace_layout.setSpacing(16)

        banner = QHBoxLayout()
        info_lbl = QLabel(f"Group: {self.group_name}  |  Instructor: {self.teacher_name}")
        info_lbl.setObjectName("HeaderTitle")
        banner.addWidget(info_lbl)
        workspace_layout.addLayout(banner)

        legend = QHBoxLayout()
        legend.setAlignment(Qt.AlignmentFlag.AlignLeft)
        legend.setSpacing(8)
        def create_pill(text: str, bg: str, fg: str, bnd: str, dashed: bool = False) -> QLabel:
            lbl = QLabel(text)
            border_style = "dashed" if dashed else "solid"
            lbl.setStyleSheet(f"background-color: {bg}; color: {fg}; font-weight: bold; font-size: 10px; border: 2px {border_style} {bnd}; border-radius: 10px; padding: 4px 10px;")
            return lbl
        legend.addWidget(create_pill("Preferred", "#EFF6FF", "#1D4ED8", "#BFDBFE"))
        legend.addWidget(create_pill("Neutral", "#FFFFFF", "#0F172A", "#CBD5E1"))
        legend.addWidget(create_pill("Dislike", "#F1F5F9", "#64748B", "#E2E8F0"))
        legend.addWidget(create_pill("Blocked / Busy", "#F8FAFC", "#94A3B8", "#CBD5E1", dashed=True))
        workspace_layout.addLayout(legend)

        card = QWidget()
        card.setObjectName("MainCard")
        self.card_grid_layout = QVBoxLayout(card)
        self.card_grid_layout.setContentsMargins(16, 16, 16, 16)
        
        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.card_grid_layout.addWidget(self.grid_container)
        
        workspace_layout.addWidget(card)
        workspace_layout.addStretch()

        footer = QHBoxLayout()
        footer.addStretch()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_confirm = QPushButton("Save Schedule Changes")
        self.btn_confirm.setObjectName("SaveBtn")
        self.btn_confirm.clicked.connect(self.accept)
        footer.addWidget(self.btn_cancel)
        footer.addWidget(self.btn_confirm)
        workspace_layout.addLayout(footer)

        main_layout.addWidget(workspace)

        self.refresh_ledger_list()
        self.rebuild_heatmap_grid()

    def refresh_ledger_list(self):
        self.ledger_table.setRowCount(0)
        for lock in self.locked_sessions:
            if lock.get("group_id") == self.group_id and lock.get("id") not in self.pending_deletions:
                self.add_ledger_row(lock, is_pending=False)
                
        for addition in self.pending_additions:
            self.add_ledger_row(addition, is_pending=True)

    # 🟢 UX REFACTOR: Standardizes timestamps cleanly to show clock times (e.g. 08:30)
    def add_ledger_row(self, session_dict: dict, is_pending: bool):
        row = self.ledger_table.rowCount()
        self.ledger_table.insertRow(row)
        
        # 1. Resolve human-readable day safely
        day_str = session_dict.get("day")
        if "day_idx" in session_dict and isinstance(session_dict["day_idx"], int):
            day_str = self.days[session_dict["day_idx"]]
            
        # 2. Extract starting clock hours directly from the slot label range
        if "slot_id" in session_dict and isinstance(session_dict["slot_id"], int):
            slot_range = self.slots[session_dict["slot_id"]]
        else:
            slot_range = str(session_dict.get("slot", ""))
            
        # Split on hyphen to pull start time (e.g. "08:30-10:30" -> "08:30")
        start_time = slot_range.split("-")[0] if "-" in slot_range else slot_range
        room_label = session_dict.get("room_name") or session_dict.get("room_id")
        
        r_item = QTableWidgetItem(room_label)
        c_item = QTableWidgetItem(f"{day_str} : {start_time}")
        
        if is_pending:
            r_item.setBackground(QBrush(QColor("#DCFCE7")))
            c_item.setBackground(QBrush(QColor("#DCFCE7")))
            
        self.ledger_table.setItem(row, 0, r_item)
        self.ledger_table.setItem(row, 1, c_item)

        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(2, 2, 2, 2)
        btn_action = QPushButton("Remove" if not is_pending else "Drop")
        btn_action.setStyleSheet("background-color: #FEE2E2; color: #B91C1C; font-weight: bold; border-radius: 4px; font-size: 10px; padding: 3px;")
        
        btn_action.clicked.connect(lambda _, s=session_dict, p=is_pending: self.handle_session_removal(s, p))
        action_layout.addWidget(btn_action)
        self.ledger_table.setCellWidget(row, 2, action_widget)

    def rebuild_heatmap_grid(self):
        if self.grid:
            while self.grid.count():
                item = self.grid.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        for col, day in enumerate(self.days):
            lbl = QLabel(day)
            lbl.setObjectName("DayHeader")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(lbl, 0, col + 1)

        for row, slot in enumerate(self.slots):
            lbl = QLabel(slot)
            lbl.setObjectName("TimeHeader")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.grid.addWidget(lbl, row + 1, 0)

            for col, day in enumerate(self.days):
                pref = self.teacher_prefs.get(day, {}).get(str(row), "neutral").lower() if isinstance(self.teacher_prefs.get(day), dict) else self.teacher_prefs.get(f"{day}_{row}", "neutral").lower()
                is_avail, reason, vacant_rooms = self.calculate_slot_availability(day, slot)
                
                if pref == "unavailable":
                    is_avail = False
                    reason = "Unavailable"
                
                if not is_avail:
                    btn = QPushButton(reason)
                    btn.setEnabled(False)
                    btn.setStyleSheet("background-color: #F8FAFC; color: #94A3B8; font-size: 10px; font-style: italic; border: 2px dashed #CBD5E1; border-radius: 6px; min-height: 44px;")
                    self.grid.addWidget(btn, row + 1, col + 1)
                else:
                    btn = QPushButton("Available")
                    btn.setCheckable(True)
                    if pref == "preferred":
                        btn.setStyleSheet("background-color: #EFF6FF; color: #1D4ED8; font-weight: bold; border: 2px solid #BFDBFE; border-radius: 6px; min-height: 44px;")
                    elif pref == "dislike":
                        btn.setStyleSheet("background-color: #F1F5F9; color: #64748B; font-weight: 500; border: 1px solid #E2E8F0; border-radius: 6px; min-height: 44px;")
                    else:
                        btn.setStyleSheet("background-color: #FFFFFF; color: #0F172A; font-weight: bold; border: 1px solid #CBD5E1; border-radius: 6px; min-height: 44px;")

                    btn.clicked.connect(lambda _, b=btn, d=day, r=row, v=vacant_rooms: self.handle_slot_selection(b, d, r, v))
                    self.grid.addWidget(btn, row + 1, col + 1)

    def calculate_slot_availability(self, day: str, slot_label: str) -> tuple:
        occupied_rooms = set()
        for item in self.current_schedule:
            if item.get("day") == day and item.get("slot") == slot_label:
                if item.get("group") == self.group_name:
                    return False, "Group Busy", []
                if item.get("teacher") == self.teacher_name:
                    return False, "Teacher Busy", []
                occupied_rooms.add(item.get("room"))
                
        for add in self.pending_additions:
            if add["day"] == day and add["slot"] == slot_label:
                occupied_rooms.add(add["room_name"])
        
        all_room_names = [rm.get("name", rm.get("id")) for rm in self.rooms]
        vacant_rooms = [r for r in all_room_names if r not in occupied_rooms]
        
        if not vacant_rooms:
            return False, "Rooms Full", []
        return True, "Available", vacant_rooms

    def handle_slot_selection(self, selected_btn: QPushButton, day: str, slot_idx: int, vacant_rooms: list):
        for r in range(1, len(self.slots) + 1):
            for c in range(1, len(self.days) + 1):
                widget = self.grid.itemAtPosition(r, c).widget()
                if isinstance(widget, QPushButton) and widget != selected_btn and widget.isCheckable():
                    widget.setChecked(False)
                elif isinstance(widget, QComboBox):
                    self.rebuild_heatmap_grid()
                    return

        if selected_btn.isChecked():
            room_picker = QComboBox()
            room_picker.addItems(["-- Select Room --"] + vacant_rooms)
            room_picker.setStyleSheet("""
                QComboBox { background-color: #EFF6FF; color: #1D4ED8; font-weight: bold; padding: 2px 6px; border: 2px solid #2563EB; border-radius: 6px; min-height: 44px; }
                QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 20px; border-left: none; }
                QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #1D4ED8; margin-top: 2px; }
                QComboBox QAbstractItemView { background-color: #FFFFFF; color: #0F172A; selection-background-color: #EFF6FF; selection-color: #1D4ED8; border: 1px solid #CBD5E1; border-radius: 6px; outline: none; }
            """)
            
            room_picker.currentTextChanged.connect(lambda txt: self.commit_new_addition(day, slot_idx, txt))
            
            self.grid.removeWidget(selected_btn)
            selected_btn.deleteLater()
            self.grid.addWidget(room_picker, slot_idx + 1, self.days.index(day) + 1)

    def commit_new_addition(self, day: str, slot_idx: int, room_name: str):
        if not room_name or "--" in room_name:
            return
            
        import uuid
        new_session = {
            "id": f"temp_{uuid.uuid4().hex[:8]}",
            "group_id": self.group_id,
            "group_name": self.group_name,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher_name,
            "room_id": room_name,
            "room_name": room_name,
            "day": day,
            "day_idx": self.days.index(day),
            "slot": self.slots[slot_idx],
            "slot_id": slot_idx
        }
        
        self.pending_additions.append(new_session)
        self.refresh_ledger_list()
        self.rebuild_heatmap_grid()

    def handle_session_removal(self, session_dict: dict, is_pending: bool):
        s_id = session_dict.get("id")
        if is_pending:
            self.pending_additions = [a for a in self.pending_additions if a.get("id") != s_id]
        else:
            self.pending_deletions.append(s_id)
            day_label = session_dict.get("day")
            slot_label = session_dict.get("slot")
            room_label = session_dict.get("room_name") or session_dict.get("room_id")
            
            self.current_schedule = [
                item for item in self.current_schedule if not (
                    item.get("day") == day_label and 
                    item.get("slot") == slot_label and 
                    item.get("room") == room_label and 
                    item.get("group") == self.group_name
                )
            ]

        self.refresh_ledger_list()
        self.rebuild_heatmap_grid()

    def get_transaction_manifest(self) -> dict:
        return {
            "additions": self.pending_additions,
            "deletions": self.pending_deletions
        }