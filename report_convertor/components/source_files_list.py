"""Source file list widget used by the template editor."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from report_convertor.models.template import SourceFile


class SourceFilesWidget(QWidget):
    """Display uploaded source workbooks for mapping."""

    def __init__(self) -> None:
        super().__init__()
        self._list = QListWidget()
        self._sources: list[SourceFile] = []
        self._from_s3 = False
        layout = QVBoxLayout()
        layout.addWidget(self._list)
        self.setLayout(layout)

    def load_sources(self, sources: list[SourceFile], from_s3: bool = False) -> None:
        """Replace the source list and its display values."""
        self._sources = list(sources)
        self._from_s3 = from_s3
        self._list.clear()
        for source in self._sources:
            self._add_item(source, from_s3)

    def _add_item(self, source: SourceFile, from_s3: bool) -> None:
        item = QListWidgetItem(f"{source.key} -> {source.file_path}")

        if not from_s3:
            path = Path(source.file_path).expanduser()
            if not path.exists():
                font = QFont()
                font.setItalic(True)
                item.setFont(font)
                item.setForeground(QColor(200, 0, 0))

        self._list.addItem(item)

    def sources(self) -> list[SourceFile]:
        """Return the configured sources."""
        return list(self._sources)

    def add_source(self, source: SourceFile) -> None:
        """Append a source workbook."""
        self._sources.append(source)
        self._add_item(source, self._from_s3)

    def remove_selected(self) -> SourceFile | None:
        """Remove and return the selected source workbook."""
        row = self._list.currentRow()
        if row < 0:
            return None
        self._list.takeItem(row)
        return self._sources.pop(row)

    def set_from_s3(self, from_s3: bool) -> None:
        """Update display when S3 toggle changes."""
        if self._from_s3 != from_s3:
            self._from_s3 = from_s3
            self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the list to apply correct styling."""
        self._list.clear()
        for source in self._sources:
            self._add_item(source, self._from_s3)
