"""S3 template selection dialog with search and version hierarchy."""

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


class S3TemplateSelectDialog(QDialog):
    """Dialog for selecting templates from S3 with search and version hierarchy."""

    def __init__(
        self, parent, items: list[dict], title: str = "Select Template from S3"
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
        self._search_input.setPlaceholderText("Type to filter templates...")
        self._search_input.textChanged.connect(self._on_search_changed)

        search_row = QHBoxLayout()
        search_row.addWidget(search_label)
        search_row.addWidget(self._search_input)
        layout.addLayout(search_row)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Name"])
        self._tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
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
        filter_lower = filter_text.lower() if filter_text else ""

        for item in self._items:
            name = item.get("name", "")
            versions = item.get("versions", [])

            if filter_lower and filter_lower not in name.lower():
                continue

            template_item = QTreeWidgetItem(self._tree, [name])
            template_item.setExpanded(True)

            for version in versions:
                version_item = QTreeWidgetItem(template_item, [version])
                version_item.setCheckState(0, Qt.CheckState.Unchecked)
                version_item.setData(
                    0, Qt.ItemDataRole.UserRole, {"name": name, "version": version}
                )

    def _on_search_changed(self, text: str) -> None:
        self._build_tree(text)

    def selected_template_version(self) -> tuple[str, str] | None:
        """Return (template_name, version) tuple for selected template version."""
        iterator = QTreeWidgetItemIterator(self._tree)
        while True:
            try:
                item = next(iterator)
            except StopIteration:
                break
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and item.checkState(0) == Qt.CheckState.Checked:
                return (data.get("name", ""), data.get("version", ""))
        return None


class QTreeWidgetItemIterator:
    """Iterator for QTreeWidget items (depth-first)."""

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
