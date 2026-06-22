# solver_worker.py
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, Any
import copy
from ceil_scheduler import run_solver

class OptimizationSolverWorker(QThread):
    # 1. Define custom signals at the class level
    log_emitted = pyqtSignal(str)
    calculation_finished = pyqtSignal(dict)
    calculation_failed = pyqtSignal(str)

    def __init__(self, raw_data_reference: Dict[str, Any], parent=None):
        # Pass parent to QThread to maintain proper Qt object tree hierarchy
        super().__init__(parent)
        self._raw_data_reference = raw_data_reference

    def run(self) -> None:
        """Executes completely in the background thread. NO UI CALLS PERMITTED."""
        try:
            # Deepcopy runs strictly in the background thread.
            data_snapshot = copy.deepcopy(self._raw_data_reference)
            
            # Execute calculation, passing our signal-emitting callback
            results = run_solver(
                data_snapshot,
                data_snapshot.get("weights", {}),
                log_cb=self.emit_progress,
            )
            
            # Emit completion signal with the results payload
            self.calculation_finished.emit(results)
            
        except Exception as e:
            import traceback
            # Emit failure signal with error details
            self.calculation_failed.emit(f"Engine Crash: {str(e)}\n{traceback.format_exc()}")

    def emit_progress(self, message: str) -> None:
        """Callback for OR-Tools to emit progress safely across the thread boundary."""
        self.log_emitted.emit(f"[OR-Tools Engine] {message}")