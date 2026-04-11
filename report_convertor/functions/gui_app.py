"""PyQt6 launcher for the desktop interface."""

from __future__ import annotations

import sys
from pathlib import Path


def run_gui(templates_dir: Path) -> int:
    """Start the GUI application.

    Args:
        templates_dir: Default directory for local template JSON files.
    """

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
