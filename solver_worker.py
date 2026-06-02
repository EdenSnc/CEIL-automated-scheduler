# solver_worker.py
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, Any
import copy
from ceil_scheduler import run_solver

class OptimizationSolverWorker(QThread):
    log_emitted = pyqtSignal(str)
    calculation_finished = pyqtSignal(dict)
    calculation_failed = pyqtSignal(str)

    def __init__(self, raw_data_reference: Dict[str, Any]):
        super().__init__()
        # Store a raw reference. DO NOT process it here.
        self._raw_data_reference = raw_data_reference

    def run(self) -> None:
        try:
            # Deepcopy now runs strictly in the background thread. UI remains smooth.
            data_snapshot = copy.deepcopy(self._raw_data_reference)
            results = run_solver(
                data_snapshot,
                data_snapshot.get("weights", {}),
                log_cb=self.emit_log,
            )
            self.calculation_finished.emit(results)
        except Exception as e:
            import traceback
            self.calculation_failed.emit(f"Engine Crash: {str(e)}\n{traceback.format_exc()}")

    def emit_log(self, message: str) -> None:
        self.log_emitted.emit(f"[OR-Tools Engine] {message}")