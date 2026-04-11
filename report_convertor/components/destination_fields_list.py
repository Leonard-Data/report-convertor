"""Destination field list widget used by the template editor."""

from __future__ import annotations

from PyQt6.QtWidgets import QListWidget, QVBoxLayout, QWidget


class DestinationFieldsWidget(QWidget):
    """Display editable destination field names."""

    def __init__(self) -> None:
        super().__init__()
        self._list = QListWidget()
        layout = QVBoxLayout()
        layout.addWidget(self._list)
        self.setLayout(layout)

    def load_fields(self, names: list[str]) -> None:
        """Replace the destination field list."""

        self._list.clear()
        self._list.addItems(names)

    def field_names(self) -> list[str]:
        """Return the destination fields in display order."""

        return [self._list.item(index).text() for index in range(self._list.count())]

    def add_field(self, name: str) -> None:
        """Append a destination field name."""

        self._list.addItem(name)

    def remove_selected(self) -> str | None:
        """Remove and return the selected destination field."""

        row = self._list.currentRow()
        if row < 0:
            return None
        item = self._list.takeItem(row)
        return item.text()
