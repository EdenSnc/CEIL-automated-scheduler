# data_manager.py
import json
import copy
import logging
import os
import ast
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
    }

    _DEFAULT_WEIGHTS: Dict[str, int] = {
        "W_GAP": 30,
        "W_PREFERENCE": 1,
        "W_LOAD_BALANCE": 20,
        "W_FAIRNESS": 15,
        "W_ROOM_CHANGE": 10,
        "W_COGNITIVE": 5,
        "W_SAME_DAY_CLUSTER": 80
    }

    def __init__(self, filepath: str = "ceil_data.json") -> None:
        if not os.path.isabs(filepath):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(base_dir, filepath)
            
        self.filepath = filepath
        self.data: Dict[str, Any] = {
            "metadata": copy.deepcopy(self._DEFAULT_METADATA),
            "weights": copy.deepcopy(self._DEFAULT_WEIGHTS),
            "teachers": [],
            "groups": [],
            "rooms": [],
            "schedule": [],
        }
        self.load_from_disk()

    def load_from_disk(self) -> None:
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as fh:
                disk_payload: Dict[str, Any] = json.load(fh)
            for key in ("metadata", "teachers", "groups", "rooms", "schedule"):
                if key in disk_payload:
                    self.data[key] = disk_payload[key]
            
            if "weights" in disk_payload:
                for k, v in disk_payload["weights"].items():
                    self.data["weights"][k] = v
        except Exception as exc:
            logger.exception("Error loading configuration data: %s", exc)

    def save_to_disk(self) -> None:
        try:
            with open(self.filepath, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, indent=4, ensure_ascii=False)
        except OSError as exc:
            logger.error("Cannot write file: %s", exc)

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

    def export_to_excel(self, filepath: str) -> None:
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                schedule = self.data.get("schedule", [])
                if schedule:
                    day_order = {"SAT": 0, "SUN": 1, "MON": 2, "TUE": 3, "WED": 4, "THU": 5}
                    days = sorted(list(set(item.get("day", "") for item in schedule)), key=lambda d: day_order.get(d.upper(), 99))
                    slots = sorted(list(set(item.get("slot", "") for item in schedule)))
                    
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
                    
                pd.DataFrame(self.data.get("teachers", [])).to_excel(writer, sheet_name="Teachers", index=False)
                pd.DataFrame(self.data.get("groups", [])).to_excel(writer, sheet_name="Groups", index=False)
                pd.DataFrame(self.data.get("rooms", [])).to_excel(writer, sheet_name="Rooms", index=False)
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            raise

    def import_master_data_from_excel(self, filepath: str) -> None:
        try:
            xls = pd.ExcelFile(filepath)
            def parse_target_sheet(sheet_name):
                if sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name)
                    df = df.where(pd.notnull(df), None)
                    records = df.to_dict(orient="records")
                    cleaned_records = []
                    for rec in records:
                        clean_r = {k: v for k, v in rec.items() if v is not None}

                        # Preserve blank language fields explicitly so they survive round-trips
                        # through Excel import/export and remain available to the UI as empty strings.
                        if "language" in rec:
                            raw_language = rec.get("language")
                            clean_r["language"] = "" if raw_language is None else str(raw_language)
                        
                        # CRITICAL FIX: Convert Excel strings back into native Python lists/dicts
                        for key in ["preferences", "allowed_days", "allowed_slots"]:
                            if key in clean_r and isinstance(clean_r[key], str):
                                try:
                                    clean_r[key] = ast.literal_eval(clean_r[key])
                                except Exception:
                                    pass # Fallback to ignore if malformed
                        cleaned_records.append(clean_r)
                    return cleaned_records
                return []

            teachers = parse_target_sheet("Teachers")
            groups = parse_target_sheet("Groups")
            rooms = parse_target_sheet("Rooms")
            
            if teachers: self.data["teachers"] = teachers
            if groups: self.data["groups"] = groups
            if rooms: self.data["rooms"] = rooms
            
            self.save_to_disk()
        except Exception as e:
            logger.error(f"Excel import failed: {e}")
            raise