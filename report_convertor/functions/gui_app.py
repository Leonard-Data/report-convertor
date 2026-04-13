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

    _apply_stylesheet(app)

    window = MainWindow(templates_dir)
    window.show()
    return app.exec()


def _apply_stylesheet(app) -> None:
    """Load and apply the dark QSS theme."""
    qss_path = Path(__file__).parent.parent / "resources" / "style.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
