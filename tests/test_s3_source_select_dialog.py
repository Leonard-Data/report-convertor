"""Tests for S3SourceSelectDialog component."""

from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt

from report_convertor.components.s3_source_select_dialog import S3SourceSelectDialog


def _make_items(*entries) -> list[dict]:
    """Build item dicts from (folder, file, key) tuples."""
    return [{"folder": f, "file": fn, "key": k} for f, fn, k in entries]


class TestS3SourceSelectDialog:
    """Test suite for S3SourceSelectDialog."""

    def test_no_selection_returns_empty(self, qtbot) -> None:
        """No boxes checked returns empty list."""
        items = _make_items(("FolderA", "report1.xlsx", "FolderA/report1.xlsx"))
        dialog = S3SourceSelectDialog(None, items)
        qtbot.addWidget(dialog)

        assert dialog.selected_files() == []

    def test_checked_file_is_returned(self, qtbot) -> None:
        """Checking a file item returns it in selected_files."""
        items = _make_items(("FolderA", "report1.xlsx", "FolderA/report1.xlsx"))
        dialog = S3SourceSelectDialog(None, items)
        qtbot.addWidget(dialog)

        folder_item = dialog._tree.topLevelItem(0)
        file_item = folder_item.child(0)
        file_item.setCheckState(0, Qt.CheckState.Checked)

        result = dialog.selected_files()
        assert result == [("FolderA", "report1.xlsx", "FolderA/report1.xlsx")]

    def test_files_across_multiple_folders_all_visited(self, qtbot) -> None:
        """Checked files in folders 2+ are included (iterator covers all top-level items)."""
        items = _make_items(
            ("FolderA", "a.xlsx", "FolderA/a.xlsx"),
            ("FolderB", "b.xlsx", "FolderB/b.xlsx"),
            ("FolderC", "c.xlsx", "FolderC/c.xlsx"),
        )
        dialog = S3SourceSelectDialog(None, items)
        qtbot.addWidget(dialog)

        # Check file in FolderB (top-level index 1) and FolderC (index 2)
        dialog._tree.topLevelItem(1).child(0).setCheckState(0, Qt.CheckState.Checked)
        dialog._tree.topLevelItem(2).child(0).setCheckState(0, Qt.CheckState.Checked)

        result = dialog.selected_files()
        assert len(result) == 2
        keys = {r[2] for r in result}
        assert keys == {"FolderB/b.xlsx", "FolderC/c.xlsx"}

    def test_checkboxes_are_user_checkable(self, qtbot) -> None:
        """File items must have ItemIsUserCheckable flag so clicks toggle state."""
        items = _make_items(("FolderA", "report.xlsx", "FolderA/report.xlsx"))
        dialog = S3SourceSelectDialog(None, items)
        qtbot.addWidget(dialog)

        file_item = dialog._tree.topLevelItem(0).child(0)
        assert file_item.flags() & Qt.ItemFlag.ItemIsUserCheckable

    def test_all_folders_expanded(self, qtbot) -> None:
        """Every folder item is expanded by default."""
        items = _make_items(
            ("FolderA", "a.xlsx", "key-a"),
            ("FolderB", "b.xlsx", "key-b"),
        )
        dialog = S3SourceSelectDialog(None, items)
        qtbot.addWidget(dialog)

        for i in range(dialog._tree.topLevelItemCount()):
            assert dialog._tree.topLevelItem(i).isExpanded()

    def test_search_filters_by_filename(self, qtbot) -> None:
        """Search box filters file items by name."""
        items = _make_items(
            ("FolderA", "alpha.xlsx", "key-alpha"),
            ("FolderA", "beta.xlsx", "key-beta"),
        )
        dialog = S3SourceSelectDialog(None, items)
        qtbot.addWidget(dialog)

        dialog._search_input.setText("alpha")

        folder_item = dialog._tree.topLevelItem(0)
        assert folder_item.childCount() == 1
        assert folder_item.child(0).text(0) == "alpha.xlsx"

    def test_multiple_files_in_same_folder(self, qtbot) -> None:
        """Multiple checked files in one folder are all returned."""
        items = _make_items(
            ("FolderA", "a.xlsx", "key-a"),
            ("FolderA", "b.xlsx", "key-b"),
            ("FolderA", "c.xlsx", "key-c"),
        )
        dialog = S3SourceSelectDialog(None, items)
        qtbot.addWidget(dialog)

        folder_item = dialog._tree.topLevelItem(0)
        folder_item.child(0).setCheckState(0, Qt.CheckState.Checked)
        folder_item.child(2).setCheckState(0, Qt.CheckState.Checked)

        result = dialog.selected_files()
        assert len(result) == 2
        assert {r[2] for r in result} == {"key-a", "key-c"}

    def test_empty_items_returns_empty(self, qtbot) -> None:
        """No items in dialog returns empty selection."""
        dialog = S3SourceSelectDialog(None, [])
        qtbot.addWidget(dialog)

        assert dialog.selected_files() == []
