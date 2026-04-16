"""PyQt6 launcher for the desktop interface."""

from __future__ import annotations

import sys
from pathlib import Path


def _install_crash_handler() -> None:
    """In frozen windowed mode stderr is null; route unhandled exceptions to a
    message box and a log file next to the exe so errors are never lost."""
    if not getattr(sys, "frozen", False):
        return

    import traceback

    log_path = Path(sys.executable).parent / "report-convertor-crash.log"

    def _excepthook(exc_type, exc_value, exc_tb) -> None:
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            log_path.write_text(text, encoding="utf-8")
        except OSError:
            pass
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            if QApplication.instance() is None:
                QApplication(sys.argv)
            QMessageBox.critical(None, "Unexpected Error", text[:2000])
        except Exception:
            pass

    sys.excepthook = _excepthook


def run_gui(templates_dir: Path) -> int:
    """Start the GUI application.

    Args:
        templates_dir: Default directory for local template JSON files.
    """
    _install_crash_handler()

    try:
        from PyQt6.QtWidgets import QApplication
        from report_convertor.components.main_window import MainWindow
    except ImportError as error:
        raise RuntimeError("PyQt6 GUI dependencies are installed but not loadable.") from error

    app = QApplication(sys.argv)
    app.setApplicationName("Report Convertor")

    window = MainWindow(templates_dir)
    window.show()
    return app.exec()
