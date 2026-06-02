# ui_components.py
import os
import hashlib
import logging
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

# ── Supported languages (used in dropdowns AND colour lookup) ─────────────────
SUPPORTED_LANGUAGES = [
    "English", "French", "Spanish", "Italian",
    "German", "Swedish", "Japanese", "Chinese", "Turkish", "Russian"
]

# Keyed by the lowercase language name for O(1) lookup
# Format: (Fill_Hex, Border_Hex, Optional_Text_Hex)
LANGUAGE_COLORS: Dict[str, tuple] = {
    "english":  ("#C0DAFE", "#71B1FA"),
    "french":   ("#FB70BF", "#FF2395"),
    "spanish":  ("#FFB554", "#FF9B30"),
    "italian":  ("#52E084", "#16A34A"),
    "german":   ("#8B7251", "#74450F"),
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


# ── FIX: QObject MUST be listed first so PyQt6's metaclass processes pyqtSignal
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
            # 🟢 ADD THIS LINE TO PROBE
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

        # Clean incoming language string
        lang = str(item_data.get("language", "")).strip().lower()

        self.text_color = "#0F172A"  # Default text color

        # Intercept missing/empty/none languages
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
            # Fallback hash for unknown languages
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

        # Explicitly target ScheduleCardWidget to protect against global stylesheet cascading
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
    run_optimization_triggered = pyqtSignal()
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
            ("W_SAME_DAY_CLUSTER", "Same-Day Clustering", "Penalizes standard groups having 2 classes on the same day."),
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

        solver_box = QGroupBox("Solver Control Center")
        solver_layout = QHBoxLayout(solver_box)
        solver_layout.setContentsMargins(16, 10, 16, 10)

        self.btn_solve = QPushButton("Compile Optimized Schedule")
        self.btn_solve.setObjectName("SolverButton")
        self.btn_solve.setMinimumWidth(300)

        solver_layout.addStretch()
        solver_layout.addWidget(self.btn_solve)
        solver_layout.addStretch()

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
        self.debug_console.setVisible(False)   # start hidden
        self.debug_layout.addWidget(self.debug_console)

        # Collapsed height = just the group-box title bar (~32 px)
        self.debug_box.setFixedHeight(32)

        def _toggle_debug(open_state: bool):
            self.debug_console.setVisible(open_state)
            self.debug_box.setFixedHeight(240 if open_state else 32)

        self.debug_box.toggled.connect(_toggle_debug)

        outer_layout.addWidget(self.debug_box)
        self.statusBar().showMessage("Platform framework targets initialized.")

        self.btn_solve.clicked.connect(lambda: self.run_optimization_triggered.emit())
        self.btn_export.clicked.connect(self.trigger_excel_egress)
        self.btn_import.clicked.connect(self.trigger_excel_ingress)

    def setup_logging_bridge(self):
        # ── FIX: store reference so GC cannot collect the handler ─────
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


# ====================================================================
# TAB COMPONENTS
# ====================================================================

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
        # ── FIX: move setDefaultSectionSize outside the loop; use Stretch
        #         on the last content column to fill available width ─────
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

    def show_add_dialog(self):
        pass

    def show_edit_dialog(self, row_idx: int):
        pass


# ── Room tab ──────────────────────────────────────────────────────────────────

class RoomManagementTab(BaseEntityManagementTab):
    def __init__(self):
        super().__init__(
            "Classrooms",
            ["Room ID", "Room Name", "Capacity"],
            ["id", "name", "capacity"])
        # "Capacity" is short – let "Room Name" stretch instead
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)            # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Capacity
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Actions

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


# ── Teacher tab ───────────────────────────────────────────────────────────────

class TeacherManagementTab(BaseEntityManagementTab):
    preferences_requested = pyqtSignal(int, str, dict)

    def __init__(self):
        super().__init__(
            "Teaching Staff",
            ["ID", "Full Name", "Weekly Hours Cap", "Skill Matrix"],
            ["id", "name", "max_hours", "skills"])
        # ── FIX: proper column widths – no empty space on the right ──
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)        # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Hours
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)            # Skills
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Actions

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


# ── Groups tab ────────────────────────────────────────────────────────────────

class GroupManagementTab(BaseEntityManagementTab):
    def __init__(self):
        super().__init__(
            "Student Groups",
            ["ID", "Cohort Alias", "Language", "CEFR Level",
             "Sessions/Wk", "Track Modifiers", "Assigned Teacher"],
            ["id", "name", "language", "level",
             "sessions_per_week", "modifiers", "teacher_name"])
        self.teacher_map: Dict[str, str] = {}

        # ── FIX: compact column widths so the table never needs a
        #         horizontal scrollbar inside the 1250 px minimum window ─
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)        # Cohort
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Language
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # CEFR
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Sessions
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Modifiers
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)            # Teacher
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Actions

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
            
            level_str = str(item.get("level", "")).strip().upper()
            bg_color = QColor("#FFFFFF")

            if level_str.startswith("A"):
                bg_color = QColor("#E6F4EA")
            elif level_str.startswith("B"):
                bg_color = QColor("#E8F0FE")
            elif level_str.startswith("C"):
                bg_color = QColor("#F3E8FF")

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

    # ── helpers shared by add/edit dialogs ───────────────────────────
    @staticmethod
    def _make_lang_combo(current_value: str = "") -> QComboBox:
        """Return a QComboBox pre-populated with every supported language."""
        cb = QComboBox()
        cb.addItems(SUPPORTED_LANGUAGES)
        # Honour whatever is stored (case-insensitive match)
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
        # ── FIX: replaced free-text QLineEdit with a proper dropdown ──
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
                "language":         lang_cb.currentText(),   # ← from dropdown
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
        # ── FIX: replaced free-text QLineEdit with a proper dropdown ──
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
                "language":         lang_cb.currentText(),   # ← from dropdown
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


# ====================================================================
# PREFERENCES MATRIX DIALOG
# ====================================================================

class TeacherPreferencesDialog(QDialog):
    def __init__(self, teacher_name: str, current_prefs: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Availability Matrix: {teacher_name}")
        self.setMinimumSize(800, 500)
        self.current_prefs = current_prefs
        self.days = ["SAT", "SUN", "MON", "TUE", "WED", "THU"]
        self.slots = ["08:30-10:30", "10:30-12:30", "13:30-15:30",
                      "15:30-17:30", "17:30-19:30"]
        self.combos = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        legend = QLabel(
            "🟢 Preferred (-10 penalty)  |  ⚪ Neutral (0 penalty)  |  "
            "🟠 Dislike (+50 penalty)  |  🔴 Unavailable (Hard Ban)")
        legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        legend.setStyleSheet(
            "padding: 10px; font-weight: bold; background: #F8FAFC; "
            "border-radius: 6px; margin-bottom: 10px;")
        layout.addWidget(legend)

        grid = QGridLayout()
        grid.setSpacing(8)

        for col, day in enumerate(self.days):
            lbl = QLabel(day)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-weight: 800; color: #475569;")
            grid.addWidget(lbl, 0, col + 1)

        for row, slot in enumerate(self.slots):
            lbl = QLabel(slot)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet("font-weight: 600; padding-right: 10px;")
            grid.addWidget(lbl, row + 1, 0)

            for col, day in enumerate(self.days):
                cb = QComboBox()
                cb.addItems(["Neutral", "Preferred", "Dislike", "Unavailable"])

                if day in self.current_prefs and isinstance(self.current_prefs[day], dict):
                    val = self.current_prefs[day].get(str(row), "neutral")
                else:
                    val = self.current_prefs.get(f"{day}_{row}", "neutral")

                cb.setCurrentText(val.capitalize())

                def update_color(c=cb):
                    t = c.currentText()
                    if t == "Preferred":
                        c.setStyleSheet("background-color: #DCFCE7; font-weight:bold;")
                    elif t == "Dislike":
                        c.setStyleSheet("background-color: #FFEDD5; font-weight:bold;")
                    elif t == "Unavailable":
                        c.setStyleSheet("background-color: #FEE2E2; color: #9F1239; font-weight:bold;")
                    else:
                        c.setStyleSheet("background-color: #FFFFFF;")

                cb.currentTextChanged.connect(lambda _, c=cb: update_color(c))
                update_color(cb)

                self.combos[f"{day}_{row}"] = cb
                grid.addWidget(cb, row + 1, col + 1)

        layout.addLayout(grid)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: #F1F5F9; color: #475569;")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save Availability")
        btn_save.clicked.connect(self.accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def get_preferences(self) -> dict:
        prefs = {}
        for day in self.days:
            prefs[day] = {}
            for row in range(len(self.slots)):
                val = self.combos[f"{day}_{row}"].currentText().lower()
                prefs[day][str(row)] = val
        return prefs
