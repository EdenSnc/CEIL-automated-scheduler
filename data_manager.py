# data_manager.py
import json
import copy
import logging
import os
import ast
import sqlite3
import threading
import uuid
from typing import Any, Dict, List
import pandas as pd
import openpyxl
from openpyxl.styles import Alignment

logger = logging.getLogger(__name__)

class ScheduleDataManager:
    _DEFAULT_METADATA: Dict[str, Any] = {
        "days": ["SAT", "SUN", "MON", "TUE", "WED", "THU"],
        "slots": [
            {"id": 0, "label": "08:30-10:30"},
            {"id": 1, "label": "10:30-12:30"},
            {"id": 2, "label": "13:30-15:30"},
            {"id": 3, "label": "15:30-17:30"},
            {"id": 4, "label": "17:30-19:30"},
        ],
        "solver_timeout": 60 # Added Execution Time State
    }

    _DEFAULT_WEIGHTS: Dict[str, int] = {
        "W_GAP": 30,
        "W_PREFERENCE": 1,
        "W_LOAD_BALANCE": 20,
        "W_FAIRNESS": 15,
        "W_ROOM_CHANGE": 10,
        "W_COGNITIVE": 5
        # W_SAME_DAY_CLUSTER removed entirely
    }

    def __init__(self, filepath: str = "ceil_scheduler.db") -> None:
        if filepath.endswith(".json"):
            filepath = filepath.replace(".json", ".db")
            
        if not os.path.isabs(filepath):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(base_dir, filepath)
            
        self.filepath = filepath
        self.lock = threading.Lock()
        
        self.data: Dict[str, Any] = {
            "metadata": copy.deepcopy(self._DEFAULT_METADATA),
            "weights": copy.deepcopy(self._DEFAULT_WEIGHTS),
            "teachers": [],
            "groups": [],
            "rooms": [],
            "schedule": [],
            "locked_sessions": [], # Added support for Pinned/Makeup Sessions
        }
        self._init_db()
        self.load_from_disk()

    def _get_connection(self):
        conn = sqlite3.connect(self.filepath)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS application_state (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    );
                """)
                conn.commit()
        except Exception as exc:
            logger.exception("Failed to initialize SQLite Database: %s", exc)

    def load_from_disk(self) -> None:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM application_state")
                rows = cursor.fetchall()
                
                if not rows:
                    return 
                    
                disk_payload = {}
                for key, val_str in rows:
                    disk_payload[key] = json.loads(val_str)
                
                for key in ("metadata", "teachers", "groups", "rooms", "schedule", "locked_sessions"):
                    if key in disk_payload:
                        self.data[key] = disk_payload[key]
                
                if "weights" in disk_payload:
                    for k, v in disk_payload["weights"].items():
                        if k != "W_SAME_DAY_CLUSTER": # Filter out legacy key if present on disk
                            self.data["weights"][k] = v
        except Exception as exc:
            logger.exception("Error loading state from SQLite: %s", exc)

    def save_to_disk(self) -> None:
        state_snapshot = copy.deepcopy(self.data)
        threading.Thread(target=self._execute_db_write, args=(state_snapshot,), daemon=True).start()

    def _execute_db_write(self, state_snapshot: Dict[str, Any]) -> None:
        with self.lock:
            try:
                with self._get_connection() as conn:
                    for key in ["metadata", "weights", "teachers", "groups", "rooms", "schedule", "locked_sessions"]:
                        payload_str = json.dumps(state_snapshot.get(key, []), ensure_ascii=False)
                        conn.execute("""
                            INSERT INTO application_state (key, value) 
                            VALUES (?, ?)
                            ON CONFLICT(key) DO UPDATE SET value=excluded.value;
                        """, (key, payload_str))
                    conn.commit()
            except Exception as exc:
                logger.error("Background SQLite save pipeline dropped a write: %s", exc)

    # ==========================================
    # --- PINNED / MAKEUP SESSION MANAGEMENT ---
    # ==========================================

    def add_locked_session(self, group_id: str, teacher_id: str, room_id: str, day_idx: int, slot_id: str) -> None:
        if "locked_sessions" not in self.data:
            self.data["locked_sessions"] = []
            
        session_data = {
            "id": str(uuid.uuid4()),
            "group_id": group_id,
            "teacher_id": teacher_id,
            "room_id": room_id,
            "day_idx": day_idx,
            "slot_id": slot_id
        }
        self.data["locked_sessions"].append(session_data)
        self.save_to_disk()

    def get_locked_sessions(self) -> list:
        return self.data.get("locked_sessions", [])

    def remove_locked_session(self, session_id: str) -> None:
        if "locked_sessions" in self.data:
            original_len = len(self.data["locked_sessions"])
            self.data["locked_sessions"] = [
                s for s in self.data["locked_sessions"] if s.get("id") != session_id
            ]
            if len(self.data["locked_sessions"]) < original_len:
                self.save_to_disk()

    # ==========================================
    # --- STANDARD ENTITY MANAGEMENT ---
    # ==========================================

    def update_weight(self, key: str, value: int) -> None:
        self.data["weights"][key] = value
        self.save_to_disk()

    def reset_weights(self) -> None:
        self.data["weights"] = copy.deepcopy(self._DEFAULT_WEIGHTS)
        self.save_to_disk()

    _ID_PREFIX: Dict[str, str] = {"teachers": "T_", "groups": "G_", "rooms": "R_"}

    def _next_id(self, collection: str) -> str:
        prefix = self._ID_PREFIX[collection]
        indices: List[int] = []
        for item in self.data[collection]:
            raw = str(item.get("id", ""))
            if raw.startswith(prefix):
                try:
                    indices.append(int(raw[len(prefix):]))
                except ValueError:
                    pass
        return f"{prefix}{max(indices) + 1 if indices else 1}"

    def add_entity(self, collection: str, entity: Dict[str, Any]) -> None:
        if collection not in self._ID_PREFIX:
            return
        entity["id"] = self._next_id(collection)
        self.data[collection].append(entity)
        self.save_to_disk()

    def update_entity(self, collection: str, index: int, updated: Dict[str, Any]) -> None:
        if collection not in self._ID_PREFIX:
            return
        items = self.data[collection]
        if not (0 <= index < len(items)):
            return
        updated["id"] = items[index]["id"]
        items[index].update(updated)
        self.save_to_disk()

    def delete_entity(self, collection: str, index: int) -> None:
        if collection not in self._ID_PREFIX:
            return
        items = self.data[collection]
        if not (0 <= index < len(items)):
            return
        items.pop(index)
        self.save_to_disk()

    # ==========================================
    # --- EXCEL I/O PIPELINE ---
    # ==========================================

    def export_to_excel(self, filepath: str) -> None:
        try:
            from openpyxl.styles import Font, PatternFill, Border, Side
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                schedule = self.data.get("schedule", [])
                if schedule:
                    day_order = {"SAT": 0, "SUN": 1, "MON": 2, "TUE": 3, "WED": 4, "THU": 5}
                    days = sorted(list(set(item.get("day", "") for item in schedule)), key=lambda d: day_order.get(d.upper(), 99))
                    slots = sorted(list(set(item.get("slot", "") for item in schedule)))
                    
                    # 1. GENERATE GRID VIEW
                    grid_df = pd.DataFrame(index=slots, columns=days)
                    grid_df.fillna("", inplace=True)
                    
                    for item in schedule:
                        d, s, r, g, t = item.get("day", ""), item.get("slot", ""), item.get("room", ""), item.get("group", ""), item.get("teacher", "")
                        entry = f"[{r}] {g} ({t})"
                        current = grid_df.at[s, d]
                        grid_df.at[s, d] = (current + "\n" + entry) if current else entry
                    
                    grid_df.to_excel(writer, sheet_name="Grid View")
                    worksheet = writer.sheets["Grid View"]
                    for row in worksheet.iter_rows():
                        for cell in row:
                            cell.alignment = Alignment(wrap_text=True, vertical='top')
                    for col in worksheet.columns:
                        worksheet.column_dimensions[col[0].column_letter].width = 32

                    # 2. GENERATE ROOM VIEW
                    rooms = sorted(list(set(item.get("room", "") for item in schedule)))
                    room_cols = []
                    for r in rooms:
                        room_cols.extend([f"{r} - Language", f"{r} - Group", f"{r} - Teacher"])
                    
                    from collections import defaultdict
                    row_groups = defaultdict(list)
                    for item in schedule:
                        row_groups[(item.get("day", ""), item.get("slot", ""))].append(item)
                        
                    rows_list = []
                    for (d, s), items in sorted(row_groups.items(), key=lambda x: (day_order.get(x[0][0].upper(), 99), x[0][1])):
                        row_dict = {"Day": d, "Time": s}
                        for item in items:
                            r = item.get("room", "")
                            row_dict[f"{r} - Language"] = item.get("language", "English")
                            row_dict[f"{r} - Group"] = item.get("group", "")
                            row_dict[f"{r} - Teacher"] = item.get("teacher", "")
                        rows_list.append(row_dict)
                        
                    pd.DataFrame(rows_list, columns=["Day", "Time"] + room_cols).to_excel(writer, sheet_name="Room View", index=False)
                    pd.DataFrame(schedule).to_excel(writer, sheet_name="Raw Schedule", index=False)
                    
                # 3. GENERATE MASTER ENTITY VIEWS (Scrub constraints completely)
                teachers_copy = copy.deepcopy(self.data.get("teachers", []))
                for t in teachers_copy:
                    t.pop("allowed_days", None)  # 🟢 Drop completely from sheet exports
                    if "allowed_slots" in t and isinstance(t["allowed_slots"], list):
                        t["allowed_slots"] = ", ".join(str(s) for s in t["allowed_slots"])
                    if "preferences" in t:
                        t["preferences"] = str(t["preferences"])
                pd.DataFrame(teachers_copy).to_excel(writer, sheet_name="Teachers", index=False)

                groups_copy = copy.deepcopy(self.data.get("groups", []))
                for g in groups_copy:
                    g.pop("allowed_days", None)  # 🟢 Drop completely from sheet exports
                    if "allowed_slots" in g and isinstance(g["allowed_slots"], list):
                        g["allowed_slots"] = ", ".join(str(s) for s in g["allowed_slots"])
                pd.DataFrame(groups_copy).to_excel(writer, sheet_name="Groups", index=False)
                
                pd.DataFrame(self.data.get("rooms", [])).to_excel(writer, sheet_name="Rooms", index=False)

                # --- STRUCTURAL INTERFACE POST-PROCESSING ---
                workbook = writer.book
                global_font = Font(name="Segoe UI", size=11)
                header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
                empty_fill  = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
                
                border_side = Side(style="thin", color="CBD5E1")
                cell_border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
                
                for sheet_name in workbook.sheetnames:
                    worksheet = workbook[sheet_name]
                    for row_idx, row in enumerate(worksheet.iter_rows(), start=1):
                        is_header = (row_idx == 1)
                        if is_header:
                            worksheet.row_dimensions[row_idx].height = 26
                        else:
                            has_newline = any(str(cell.value).find('\n') != -1 for cell in row if cell.value)
                            if not has_newline:
                                worksheet.row_dimensions[row_idx].height = 20
                                
                        for cell in row:
                            if is_header:
                                cell.font = header_font
                                cell.fill = header_fill
                            else:
                                cell.font = global_font
                                cell.fill = empty_fill
                            cell.border = cell_border
                            
                    if sheet_name != "Grid View":
                        for col in worksheet.columns:
                            max_length = 0
                            col_letter = col[0].column_letter
                            for cell in col:
                                if cell.value:
                                    lines = str(cell.value).split('\n')
                                    for line in lines:
                                        if len(line) > max_length:
                                            max_length = len(line)
                            worksheet.column_dimensions[col_letter].width = max(max_length + 4, 12)

        except Exception as e:
            logger.error(f"Excel export configuration crashed: {e}")
            raise

    def import_master_data_from_excel(self, filepath: str) -> None:
        try:
            xls = pd.ExcelFile(filepath)
            
            # 🟢 RECONCILE TIMETABLE ROUND-TRIP OVERRIDES
            if "Raw Schedule" in xls.sheet_names:
                sched_df = pd.read_excel(xls, "Raw Schedule")
                sched_df = sched_df.where(pd.notnull(sched_df), None)
                raw_assignments = sched_df.to_dict(orient="records")
                
                clean_assignments = []
                for a in raw_assignments:
                    clean_a = {k: v for k, v in a.items() if v is not None}
                    if clean_a:
                        clean_assignments.append(clean_a)
                
                self.data["schedule"] = clean_assignments
                logger.info(f"[Import Pipeline] Successfully synchronized {len(clean_assignments)} rows into active schedule collection.")

            def parse_target_sheet(sheet_name):
                if sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name)
                    df = df.where(pd.notnull(df), None)
                    records = df.to_dict(orient="records")
                    cleaned_records = []
                    for rec in records:
                        clean_r = {k: v for k, v in rec.items() if v is not None}

                        if "language" in rec:
                            raw_language = rec.get("language")
                            clean_r["language"] = "" if raw_language is None else str(raw_language)
                        
                        # 🛡️ DEFENSIVE GUARD: Ensure allowed_days never pollutes the DB again
                        clean_r.pop("allowed_days", None)
                        
                        if "allowed_slots" in clean_r:
                            val_str = str(clean_r["allowed_slots"]).replace("[", "").replace("]", "").replace("'", "")
                            if val_str.strip() == "":
                                clean_r["allowed_slots"] = []
                            else:
                                tokens = [t.strip() for t in val_str.split(",")]
                                int_slots = []
                                for t in tokens:
                                    try:
                                        int_slots.append(int(float(t)))
                                    except ValueError:
                                        pass
                                clean_r["allowed_slots"] = int_slots

                        if "preferences" in clean_r and isinstance(clean_r["preferences"], str):
                            try:
                                clean_r["preferences"] = ast.literal_eval(clean_r["preferences"])
                            except Exception:
                                pass 
                        cleaned_records.append(clean_r)
                    return cleaned_records
                return []

            teachers = parse_target_sheet("Teachers")
            groups = parse_target_sheet("Groups")
            rooms = parse_target_sheet("Rooms")
            
            # Sanitize internal running states
            if teachers:
                for t in teachers: t.pop("allowed_days", None)
                self.data["teachers"] = teachers
            if groups:
                for g in groups: g.pop("allowed_days", None)
                self.data["groups"] = groups
            if rooms: 
                self.data["rooms"] = rooms
            
            self.save_to_disk()
            logger.info("[Import Pipeline] Complete workbook synchronization routine executed successfully.")
        except Exception as e:
            logger.error(f"Excel import failed: {e}")
            raise