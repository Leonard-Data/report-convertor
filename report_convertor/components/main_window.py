"""Small main-window shell that hosts the template editor."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QMainWindow, QStatusBar

from report_convertor.components.template_editor import TemplateEditorWidget


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self, templates_dir: Path) -> None:
        super().__init__()
        self.setWindowTitle("Report Convertor")
        self.resize(1100, 720)
        self.setStatusBar(QStatusBar())
        self.editor = TemplateEditorWidget(templates_dir, self.statusBar().showMessage)
        self.setCentralWidget(self.editor)
        self.template_input = self.editor.template_path_input
        self.preview_rows_input = self.editor.preview_rows_input
        self.summary_label = self.editor.summary_label
        self.mappings_table = self.editor.mapping_editor
        self.preview_table = self.editor.preview_table
