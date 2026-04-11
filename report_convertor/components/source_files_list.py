"""Source file list widget used by the template editor."""

from __future__ import annotations

from PyQt6.QtWidgets import QListWidget, QVBoxLayout, QWidget

from report_convertor.models.template import SourceFile


class SourceFilesWidget(QWidget):
    """Display uploaded source workbooks for mapping."""

    def __init__(self) -> None:
        super().__init__()
        self._list = QListWidget()
        self._sources: list[SourceFile] = []
        layout = QVBoxLayout()
        layout.addWidget(self._list)
        self.setLayout(layout)

    def load_sources(self, sources: list[SourceFile]) -> None:
        """Replace the source list and its display values."""

        self._sources = list(sources)
        self._list.clear()
        for source in self._sources:
            self._list.addItem(f"{source.key} -> {source.file_path}")

    def sources(self) -> list[SourceFile]:
        """Return the configured sources."""

        return list(self._sources)

    def add_source(self, source: SourceFile) -> None:
        """Append a source workbook."""

        self._sources.append(source)
        self._list.addItem(f"{source.key} -> {source.file_path}")

    def remove_selected(self) -> SourceFile | None:
        """Remove and return the selected source workbook."""

        row = self._list.currentRow()
        if row < 0:
            return None
        self._list.takeItem(row)
        return self._sources.pop(row)
