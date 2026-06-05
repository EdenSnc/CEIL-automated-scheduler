# controllers.py
from PyQt6.QtWidgets import QMessageBox, QDialog
from data_manager import ScheduleDataManager
from ui_components import SchedulingStudioMainWindow, TeacherPreferencesDialog
from solver_worker import OptimizationSolverWorker
from typing import Dict, Any

class SchedulingSystemController:
    def __init__(self, model: ScheduleDataManager, view: SchedulingStudioMainWindow):
        self.model = model
        self.view = view
        self.solver_worker = None
        self.bind_signals()
        self.refresh_ui_contexts()

    def bind_signals(self) -> None:
        self.view.weight_changed.connect(self.model.update_weight)
        
        # Now passing the time out limit directly from the UI button emission
        self.view.run_optimization_triggered.connect(self.launch_solver_thread) 
        
        self.view.export_excel_triggered.connect(self.handle_excel_export)
        self.view.import_excel_triggered.connect(self.handle_excel_import)
        
        self.view.btn_reset_weights.clicked.connect(self.handle_reset_weights)

        self.view.teacher_tab.preferences_requested.connect(self.handle_teacher_preferences)
        self.view.teacher_tab.create_requested.connect(lambda data: self.add_entity_handler("teachers", data))
        self.view.teacher_tab.update_requested.connect(lambda entity_id, data: self.update_entity_handler("teachers", entity_id, data))
        self.view.teacher_tab.delete_requested.connect(lambda entity_id: self.delete_entity_handler("teachers", entity_id))

        self.view.group_tab.create_requested.connect(lambda data: self.add_entity_handler("groups", data))
        self.view.group_tab.update_requested.connect(lambda entity_id, data: self.update_entity_handler("groups", entity_id, data))
        self.view.group_tab.delete_requested.connect(lambda entity_id: self.delete_entity_handler("groups", entity_id))

        self.view.group_tab.makeup_requested.connect(self.handle_makeup_dialog_flow)


        self.view.room_tab.create_requested.connect(lambda data: self.add_entity_handler("rooms", data))
        self.view.room_tab.update_requested.connect(lambda entity_id, data: self.update_entity_handler("rooms", entity_id, data))
        self.view.room_tab.delete_requested.connect(lambda entity_id: self.delete_entity_handler("rooms", entity_id))

    def handle_reset_weights(self) -> None:
        # 1. Reset the penalty weights in the database model
        self.model.reset_weights()
        
        # 2. Reset the execution timeout in the model metadata to default (60)
        if "metadata" not in self.model.data:
            self.model.data["metadata"] = {}
        self.model.data["metadata"]["solver_timeout"] = 45
        self.model.save_to_disk()
        
        # 3. Synchronize the UI components
        self.view.set_weights_ui_values(self.model.data.get("weights", {}))
        self.view.time_slider.setValue(45)  # <-- This line fixes your bug!
        
        self.view.append_log_message(

            "[System Activity] Reset all optimization penalty coefficients and solver execution limits to system defaults."
        )

    def refresh_ui_contexts(self) -> None:
        teacher_lookup_map = {t["id"]: t["name"] for t in self.model.data["teachers"]}
        self.view.group_tab.set_teacher_map(teacher_lookup_map)

        self.view.teacher_tab.render_data(self.model.data["teachers"])
        self.view.group_tab.render_data(self.model.data["groups"])
        self.view.room_tab.render_data(self.model.data["rooms"])

        if self.model.data.get("schedule"):
            live_group_langs = {}
            for g in self.model.data.get("groups", []):
                g_name = g.get("name", g.get("id"))
                live_group_langs[g_name] = g.get("language", "")

            for sched_item in self.model.data["schedule"]:
                grp_name = sched_item.get("group")
                if grp_name in live_group_langs:
                    sched_item["language"] = live_group_langs[grp_name]

            self.view.display_schedule(self.model.data["schedule"])

        # Populate the weights grid
        self.view.set_weights_ui_values(self.model.data.get("weights", {}))
        
        # Populate the execution time slider state
        timeout = self.model.data.get("metadata", {}).get("solver_timeout", 60)
        self.view.time_slider.setValue(timeout)

    def add_entity_handler(self, collection: str, data: dict) -> None:
        self.model.add_entity(collection, data)
        self.model.save_to_disk()
        self.refresh_ui_contexts()

        target_name = data.get("name", data.get("id", "New entry"))
        collection_label = collection.rstrip("s").capitalize()
        self.view.append_log_message(
            f"[System Activity] Added {collection_label} record '{target_name}' and saved the updated data to the internal database."
        )

    def update_entity_handler(self, collection: str, index: int, data: dict) -> None:
        self.model.update_entity(collection, index, data)
        self.model.save_to_disk()
        self.refresh_ui_contexts()

        target_name = data.get("name", data.get("id", f"Index {index}"))
        collection_label = collection.rstrip("s").capitalize()
        self.view.append_log_message(
            f"[System Activity] Updated {collection_label} record '{target_name}' and saved the changes."
        )

    def delete_entity_handler(self, collection: str, index: int) -> None:
        deleted_item = None
        if 0 <= index < len(self.model.data.get(collection, [])):
            deleted_item = self.model.data[collection][index]

        self.model.delete_entity(collection, index)
        self.model.save_to_disk()
        self.refresh_ui_contexts()

        target_name = "the selected record"
        if isinstance(deleted_item, dict):
            target_name = deleted_item.get("name", deleted_item.get("id", target_name))
        collection_label = collection.rstrip("s").capitalize()
        self.view.append_log_message(
            f"[System Activity] Deleted {collection_label} record '{target_name}'."
        )

    def handle_teacher_preferences(self, index: int, name: str, current_prefs: dict) -> None:
            dialog = TeacherPreferencesDialog(name, current_prefs, self.view)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_matrix = dialog.get_preferences()
                self.model.data["teachers"][index]["preferences"] = updated_matrix
                self.model.save_to_disk()
                self.refresh_ui_contexts()
                
                # 🟢 PUSH LIVE CONFIRMATION INTO SYSTEM TRACE LOG PANEL & TERMINAL CONSOLE
                self.view.append_log_message(
                    f"[System Activity] Successfully updated and saved availability matrix preferences for teacher: '{name}' (Index: {index})."
                )

    def handle_excel_export(self, filepath: str) -> None:
        try:
            self.model.export_to_excel(filepath)
            QMessageBox.information(self.view, "Export Complete", f"Data exported successfully to:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self.view, "Export Failed", f"Could not write to file:\n{str(e)}")

    def handle_excel_import(self, filepath: str) -> None:
        try:
            self.model.import_master_data_from_excel(filepath)
            self.refresh_ui_contexts()
            QMessageBox.information(self.view, "Import Success", "Master tracking matrices imported and re-synchronized from workbook.")
        except Exception as e:
            QMessageBox.critical(self.view, "Import Failed", f"Failed to parse target template:\n{str(e)}")

    def launch_solver_thread(self, timeout: int) -> None:
        # Update the metadata in the model before sending to solver
        if "metadata" not in self.model.data:
            self.model.data["metadata"] = {}
        self.model.data["metadata"]["solver_timeout"] = timeout
        self.model.save_to_disk()
        
        # Lock Engine Controls & Navigation
        self.view.btn_solve.setEnabled(False)
        self.view.weights_box.setEnabled(False)
        self.view.tabs.setEnabled(False)
        self.view.time_slider.setEnabled(False)
        for btn in self.view.day_buttons:
            btn.setEnabled(False)
        
        self.view.teacher_tab.setEnabled(False)
        self.view.group_tab.setEnabled(False)
        self.view.room_tab.setEnabled(False)
        self.view.btn_import.setEnabled(False)
        self.view.btn_export.setEnabled(False)
        
        self.view.status_text.setText("Solving matrix...")
        self.view.status_dot.setStyleSheet("color: #D97706;") 
        
        self.solver_worker = OptimizationSolverWorker(self.model.data)
        
        self.view.debug_box.setChecked(True)
        self.solver_worker.log_emitted.connect(self.view.append_log_message)
        self.solver_worker.calculation_finished.connect(self.on_solver_success)
        self.solver_worker.calculation_failed.connect(self.on_solver_failure)
        self.solver_worker.start()

    def on_solver_success(self, runtime_payload: Dict[str, Any]) -> None:
        self.view.btn_solve.setEnabled(True)
        self.view.weights_box.setEnabled(True)
        self.view.time_slider.setEnabled(True)
        self.view.teacher_tab.setEnabled(True)
        self.view.group_tab.setEnabled(True)
        self.view.room_tab.setEnabled(True)
        self.view.btn_import.setEnabled(True)
        self.view.btn_export.setEnabled(True)
        self.view.tabs.setEnabled(True)
        for btn in self.view.day_buttons:
            btn.setEnabled(True)
        
        if runtime_payload.get("status") == "SUCCESS":
            self.view.status_text.setText("Engine Ready")
            self.view.status_dot.setStyleSheet("color: #10B981;") 
            
            generated_schedule = runtime_payload.get("schedule", [])
            self.model.data["schedule"] = generated_schedule
            
            self.model.save_to_disk()
            self.view.append_log_message("[System] Optimization configurations successfully written to disk storage.")
            
            self.view.display_schedule(generated_schedule)
            status_bar = self.view.statusBar()
            if status_bar:
                status_bar.showMessage("Timetable updated successfully.")
            QMessageBox.information(self.view, "Success", "A new optimized schedule configuration has been built.")
        else:
            self.view.status_text.setText("Conflict Detected")
            self.view.status_dot.setStyleSheet("color: #F59E0B;") 
            status_bar = self.view.statusBar()
            if status_bar:
                status_bar.showMessage("Could not find a valid schedule.")
            
            reason_text = runtime_payload.get("reason", "No specific bottlenecks detected.")
            msg_box = QMessageBox(self.view)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Scheduling Conflict Detected")
            msg_box.setText("The solver could not find a valid arrangement matching the active constraints.")
            msg_box.setInformativeText("An automated structural analysis was performed on your dataset rules.")
            msg_box.setDetailedText(reason_text)
            msg_box.setStyleSheet("QPushButton { min-width: 90px; padding: 6px; }")
            msg_box.exec()

    def on_solver_failure(self, error_message: str) -> None:
        self.view.btn_solve.setEnabled(True)
        self.view.weights_box.setEnabled(True)
        self.view.time_slider.setEnabled(True)
        self.view.teacher_tab.setEnabled(True)
        self.view.group_tab.setEnabled(True)
        self.view.room_tab.setEnabled(True)
        self.view.btn_import.setEnabled(True)
        self.view.tabs.setEnabled(True)
        for btn in self.view.day_buttons:
            btn.setEnabled(True)
        
        self.view.status_text.setText("System Error")
        self.view.status_dot.setStyleSheet("color: #9F1239;") 
        QMessageBox.critical(self.view, "Error", f"An unexpected exception occurred inside optimization pipeline thread:\n{error_message}")

    def handle_makeup_dialog_flow(self, index: int) -> None:
        from ui_components import GroupMakeupManagerDialog
        from PyQt6.QtWidgets import QDialog, QMessageBox
        
        group_item = self.model.data["groups"][index]
        group_id = group_item.get("id")
        group_name = group_item.get("name", group_id)
        target_teacher_id = group_item.get("teacher_id")
        
        teacher_prefs = {}
        teacher_name = "Unassigned"
        for teacher in self.model.data["teachers"]:
            if teacher.get("id") == target_teacher_id:
                teacher_prefs = teacher.get("preferences", {})
                teacher_name = teacher.get("name", "Unknown")
                break

        dialog = GroupMakeupManagerDialog(
            group_id=group_id,
            group_name=group_name,
            teacher_id=target_teacher_id,
            teacher_name=teacher_name,
            is_ielts=group_item.get("is_ielts", False), # 🟢 Pass IELTS flag
            rooms=self.model.data["rooms"],
            current_schedule=self.model.data.get("schedule", []),
            locked_sessions=self.model.data.get("locked_sessions", []),
            teacher_prefs=teacher_prefs,
            parent=self.view
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            manifest = dialog.get_transaction_manifest()
            changes_occurred = False
            
            # 1. PROCESS BATCH DELETIONS
            if manifest["deletions"]:
                changes_occurred = True
                active_locks = self.model.data.get("locked_sessions", [])
                dead_locks = [lock for lock in active_locks if lock.get("id") in manifest["deletions"]]
                
                self.model.data["locked_sessions"] = [lock for lock in active_locks if lock.get("id") not in manifest["deletions"]]
                
                # 🟢 BULLETPROOF UI SCRUBBER: Catches both names and raw IDs seamlessly
                active_schedule = self.model.data.get("schedule", [])
                for dl in dead_locks:
                    dl_grp = dl.get("group_name") or dl.get("group_id")
                    dl_rm = dl.get("room_name") or dl.get("room_id")
                    
                    for item in list(active_schedule):
                        grp_match = (item.get("group") == dl_grp or item.get("group") == dl.get("group_id"))
                        rm_match = (item.get("room") == dl_rm or item.get("room") == dl.get("room_id"))
                        
                        if grp_match and rm_match and item.get("day") == dl.get("day") and item.get("slot") == dl.get("slot"):
                            active_schedule.remove(item)
                            
                self.model.data["schedule"] = active_schedule
                
                for dl in dead_locks:
                    g_lbl = dl.get("group_name") or dl.get("group_id", "Unknown")
                    t_lbl = dl.get("teacher_name") or dl.get("teacher_id", "Unknown")
                    r_lbl = dl.get("room_name") or dl.get("room_id", "Unknown")
                    day_lbl = dl.get("day", "Unknown Day")
                    slot_range = str(dl.get("slot", ""))
                    start_time = slot_range.split("-")[0] if "-" in slot_range else slot_range
                    self.view.append_log_message(f"[System Activity] ❌ Unpinned Makeup Exception: Group '{g_lbl}' | Instructor: {t_lbl} | {day_lbl} @ {start_time} | Room: {r_lbl}.")

            # 2. PROCESS BATCH ADDITIONS
            if manifest["additions"]:
                changes_occurred = True
                if "locked_sessions" not in self.model.data:
                    self.model.data["locked_sessions"] = []
                if "schedule" not in self.model.data:
                    self.model.data["schedule"] = []
                    
                for add in manifest["additions"]:
                    import uuid
                    db_lock_payload = {
                        "id": str(uuid.uuid4()),
                        "group_id": add["group_id"],
                        "group_name": add["group_name"],
                        "teacher_id": add["teacher_id"],
                        "teacher_name": add["teacher_name"],
                        "room_id": add["room_id"],
                        "room_name": add["room_name"],
                        "day": add["day"],
                        "day_idx": add["day_idx"],
                        "slot": add["slot"],
                        "slot_id": add["slot_id"]
                    }
                    self.model.data["locked_sessions"].append(db_lock_payload)
                    
                    self.model.data["schedule"].append({
                        "group": add["group_name"],
                        "teacher": add["teacher_name"],
                        "room": add["room_name"],
                        "day": add["day"],
                        "slot": add["slot"],
                        "language": group_item.get("language", "English")
                    })
                    
                    slot_range = str(add.get("slot", ""))
                    start_time = slot_range.split("-")[0] if "-" in slot_range else slot_range
                    self.view.append_log_message(f"[System Activity] 📌 Pinned Exceptional Makeup: Group '{add['group_name']}' | Instructor: {add['teacher_name']} | {add['day']} @ {start_time} | Room: {add['room_name']}.")

            # 3. ATOMIC WRITE & WINDOW REDRAW
            if changes_occurred:
                self.model.save_to_disk()
                self.view.display_schedule(self.model.data["schedule"])