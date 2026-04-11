"""Editable mapping table for template authoring."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHeaderView, QTableWidget, QTableWidgetItem

from report_convertor.components.searchable_combo_box import SearchableComboBox
from report_convertor.models.template import DraftMapping, TemplateDraft


class EditableMappingTableWidget(QTableWidget):
    """Edit mappings between destination fields and source workbook columns."""

    mapping_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__(0, 3)
        self._loading = False
        self._source_columns: dict[str, list[str]] = {}
        self.setHorizontalHeaderLabels(["Destination Field", "Source File", "Source Column"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def load_draft(
        self,
        template: TemplateDraft,
        source_columns: dict[str, list[str]],
    ) -> None:
        """Render mapping rows from a draft template."""

        self._loading = True
        self._source_columns = source_columns
        source_keys = [""] + [source.key for source in template.sources]
        self.setRowCount(len(template.mappings))
        for row, mapping in enumerate(template.mappings):
            self.setItem(row, 0, QTableWidgetItem(mapping.destination_field))
            source_combo = QComboBox()
            source_combo.addItems(source_keys)
            source_combo.setCurrentText(mapping.source_key or "")
            source_combo.currentTextChanged.connect(
                lambda value, index=row: self._update_column_choices(index, value),
            )
            self.setCellWidget(row, 1, source_combo)

            column_combo = SearchableComboBox()
            column_combo.currentTextChanged.connect(self._emit_mapping_changed)
            self.setCellWidget(row, 2, column_combo)
            self._update_column_choices(row, mapping.source_key or "", mapping.source_column)
        self._loading = False

    def read_mappings(self) -> list[DraftMapping]:
        """Read the current editable mapping state."""

        rows = []
        for row in range(self.rowCount()):
            destination_field = self.item(row, 0).text()
            source_combo = self.cellWidget(row, 1)
            column_combo = self.cellWidget(row, 2)
            rows.append(
                DraftMapping(
                    destination_field=destination_field,
                    source_key=source_combo.currentText() or None,
                    source_column=column_combo.currentText() or None,
                ),
            )
        return rows

    def clear_source(self, source_key: str) -> None:
        """Clear mappings that reference a removed source key."""

        for row in range(self.rowCount()):
            source_combo = self.cellWidget(row, 1)
            if source_combo.currentText() == source_key:
                source_combo.setCurrentText("")

    def _emit_mapping_changed(self) -> None:
        if not self._loading:
            self.mapping_changed.emit()

    def _update_column_choices(
        self,
        row: int,
        source_key: str,
        selected_column: str | None = None,
    ) -> None:
        column_combo = self.cellWidget(row, 2)
        columns = self._source_columns.get(source_key, [])
        current = selected_column or column_combo.currentText()
        column_combo.set_items(columns)
        column_combo.setCurrentText(current if current in columns else "")
        self._emit_mapping_changed()
