# main.py
import sys
import os
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from theme import QSS_STYLE
from data_manager import ScheduleDataManager
from ui_components import SchedulingStudioMainWindow
from controllers import SchedulingSystemController


def bootstrap_application() -> None:
    """Main application bootstrap routine with native platform taskbar fixes."""

    # Force Windows shell to decouple this process from generic python.exe grouping
    if sys.platform == "win32":
        import ctypes
        try:
            app_id = "ceil.timetable.scheduler.assistant.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception as e:
            print(f"[WARNING] Could not apply native shell process ID override: {e}")

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS_STYLE)

    icon_filename = "icon-ceil-removebg-preview.png"
    if os.path.exists(icon_filename):
        app.setWindowIcon(QIcon(icon_filename))

    # FIX: Restore Python's default SIGINT handler so Ctrl+C terminates cleanly
    # without a messy traceback.  The try/except approach does NOT work inside
    # Qt's event loop because app.exec() never returns while the loop is running.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    model_instance = ScheduleDataManager(filepath="ceil_scheduler.db")
    view_instance  = SchedulingStudioMainWindow()
    _controller    = SchedulingSystemController(model=model_instance, view=view_instance)

    view_instance.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    bootstrap_application()
