"""Tests for SearchableComboBox component."""

import pytest

from report_convertor.components.searchable_combo_box import SearchableComboBox


class TestSearchableComboBox:
    """Test suite for SearchableComboBox."""

    def test_set_items_populates_options(self, sample_combo_items: list[str]) -> None:
        """Verify items are added to combo box."""

        widget = SearchableComboBox()
        widget.set_items(sample_combo_items)

        assert widget.count() == 5

    def test_set_items_first_item(self, sample_combo_items: list[str]) -> None:
        """Verify first item is correct."""

        widget = SearchableComboBox()
        widget.set_items(sample_combo_items)

        assert widget.itemText(0) == "Option A"

    def test_set_items_clears_previous(self, sample_combo_items: list[str]) -> None:
        """Setting new items clears old items."""

        widget = SearchableComboBox()
        widget.set_items(sample_combo_items)

        widget.set_items(["New Item"])

        assert widget.count() == 1
        assert widget.itemText(0) == "New Item"

    def test_set_items_empty_list(self) -> None:
        """Handle empty list."""

        widget = SearchableComboBox()
        widget.set_items([])

        assert widget.count() == 0

    def test_completer_case_insensitive(self) -> None:
        """Verify completer is case insensitive."""

        from PyQt6.QtCore import Qt

        widget = SearchableComboBox(items=["Apple", "Banana", "Cherry"])
        completer = widget.completer()

        assert completer.caseSensitivity() == Qt.CaseSensitivity.CaseInsensitive

    def test_completer_filter_mode_contains(self) -> None:
        """Verify completer uses contains filter mode."""

        from PyQt6.QtCore import Qt

        widget = SearchableComboBox(items=["Apple", "Banana", "Cherry"])
        completer = widget.completer()

        assert completer.filterMode() == Qt.MatchFlag.MatchContains

    def test_constructor_with_items(self, sample_combo_items: list[str]) -> None:
        """Verify constructor accepts initial items."""

        widget = SearchableComboBox(items=sample_combo_items)

        assert widget.count() == 5

    def test_is_editable(self) -> None:
        """Combo box should be editable."""

        widget = SearchableComboBox()

        assert widget.isEditable()
