"""Reusable searchable combo box for large option lists."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QCompleter


class SearchableComboBox(QComboBox):
    """Editable combo box with substring filtering support."""

    def __init__(self, items: list[str] | None = None) -> None:
        """Create a combo box with optional initial items.

        Args:
            items: Optional list of entries shown in the combo box.
        """

        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        completer = QCompleter(self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(completer)
        self.set_items(items or [])

    def set_items(self, items: list[str]) -> None:
        """Replace the available combo box options.

        Args:
            items: Full list of options to display.
        """

        self.clear()
        self.addItems(items)
        model = self.model()
        if self.completer() is not None:
            self.completer().setModel(model)
