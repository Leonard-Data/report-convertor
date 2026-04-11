"""S3 source file selection dialog with search and folder hierarchy."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)


class S3SourceSelectDialog(QDialog):
    """Dialog for selecting source files from S3 with search and folder hierarchy."""

    def __init__(
        self, parent, items: list[dict], title: str = "Select Source Reports"
    ) -> None:
        super().__init__(parent)
        self._items = items
        self.setWindowTitle(title)
        self.setMinimumSize(500, 400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        search_label = QLabel("Search:")
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type to filter files...")
        self._search_input.textChanged.connect(self._on_search_changed)

        search_row = QHBoxLayout()
        search_row.addWidget(search_label)
        search_row.addWidget(self._search_input)
        layout.addLayout(search_row)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Name"])
        self._tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self._tree.setAlternatingRowColors(True)
        layout.addWidget(self._tree)

        self._build_tree()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_tree(self, filter_text: str = "") -> None:
        self._tree.clear()
        folders: dict[str, QTreeWidgetItem] = {}

        filter_lower = filter_text.lower() if filter_text else ""

        for item in self._items:
            folder = item.get("folder", "")
            filename = item.get("file", "")
            key = item.get("key", "")

            if filter_lower and filter_lower not in filename.lower():
                continue

            if folder:
                if folder not in folders:
                    folder_item = QTreeWidgetItem(self._tree, [folder])
                    folder_item.setExpanded(True)
                    folders[folder] = folder_item
                parent = folders[folder]
            else:
                parent = self._tree

            file_item = QTreeWidgetItem(parent, [filename])
            file_item.setCheckState(0, Qt.CheckState.Unchecked)
            file_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {"key": key, "folder": folder, "file": filename},
            )

    def _on_search_changed(self, text: str) -> None:
        self._build_tree(text)

    def selected_files(self) -> list[tuple[str, str, str]]:
        """Return list of (folder, filename, key) tuples for selected files."""
        selected = []
        iterator = QTreeWidgetItemIterator(self._tree)
        while True:
            try:
                item = next(iterator)
            except StopIteration:
                break
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data:
                key = data.get("key", "")
                folder = data.get("folder", "")
                filename = data.get("file", "")
                if key and item.checkState(0) == Qt.CheckState.Checked:
                    selected.append((folder, filename, key))
        return selected


class QTreeWidgetItemIterator:
    """Iterator for QTreeWidget items."""

    def __init__(self, tree: QTreeWidget) -> None:
        self._stack = []
        if tree.topLevelItemCount() > 0:
            self._stack.append(tree.topLevelItem(0))

    def __iter__(self):
        return self

    def __next__(self) -> QTreeWidgetItem:
        if not self._stack:
            raise StopIteration
        item = self._stack.pop(0)
        for i in range(item.childCount() - 1, -1, -1):
            self._stack.insert(0, item.child(i))
        return item
