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
        self._selected_item = None
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
        self._tree.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._tree)

        self._build_tree()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self._on_ok_clicked)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_ok_clicked(self) -> None:
        """Store selection when OK is clicked."""
        item = self._tree.currentItem()
        if item is None:
            selected = self._tree.selectedItems()
            if selected:
                item = selected[0]

        if item:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data:
                if data.get("version") is None and item.childCount() > 0:
                    first_child = item.child(0)
                    data = first_child.data(0, Qt.ItemDataRole.UserRole)
                self._selected_item = data
        self.accept()

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
            template_item.setData(
                0, Qt.ItemDataRole.UserRole, {"name": name, "version": None}
            )

            for version in versions:
                version_item = QTreeWidgetItem(template_item, [version])
                version_item.setData(
                    0, Qt.ItemDataRole.UserRole, {"name": name, "version": version}
                )

        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.itemActivated.connect(self._on_item_clicked)
        self._tree.currentItemChanged.connect(self._on_current_item_changed)

    def _on_current_item_changed(
        self, current: QTreeWidgetItem, previous: QTreeWidgetItem
    ) -> None:
        """Handle tree selection change."""
        if current:
            data = current.data(0, Qt.ItemDataRole.UserRole)
            if data:
                self._selected_item = data
                if data.get("version") is None and current.childCount() > 0:
                    first_child = current.child(0)
                    child_data = first_child.data(0, Qt.ItemDataRole.UserRole)
                    if child_data:
                        self._selected_item = child_data

    def _on_search_changed(self, text: str) -> None:
        self._build_tree(text)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        print("Item clicked:", data)
        if data:
            self._selected_item = data
            if data.get("version") is None:
                if item.childCount() > 0:
                    first_child = item.child(0)
                    child_data = first_child.data(0, Qt.ItemDataRole.UserRole)
                    if child_data:
                        self._selected_item = child_data

    def selected_template_version(self) -> tuple[str, str] | None:
        """Return (template_name, version) tuple for selected template version."""
        print("Selected item in dialog:", self._selected_item)
        if self._selected_item:
            name = self._selected_item.get("name", "")
            version = self._selected_item.get("version")
            if name and version:
                return (name, version)
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
