"""Tests for PreviewTableWidget component."""

import pytest

from report_convertor.components.mapping_table import PreviewTableWidget


class TestPreviewTableWidget:
    """Test suite for PreviewTableWidget."""

    def test_load_rows_with_data(self, sample_rows: list[dict[str, object]]) -> None:
        """Verify preview rows are loaded into table."""

        widget = PreviewTableWidget()
        widget.load_rows(sample_rows)

        assert widget.rowCount() == 2
        assert widget.columnCount() == 2

    def test_load_rows_column_headers(
        self, sample_rows: list[dict[str, object]]
    ) -> None:
        """Verify column headers from row keys."""

        widget = PreviewTableWidget()
        widget.load_rows(sample_rows)

        assert widget.horizontalHeaderItem(0).text() == "Employee Name"
        assert widget.horizontalHeaderItem(1).text() == "Work Email"

    def test_load_rows_cell_values(self, sample_rows: list[dict[str, object]]) -> None:
        """Verify cell values match row data."""

        widget = PreviewTableWidget()
        widget.load_rows(sample_rows)

        assert widget.item(0, 0).text() == "Alice"
        assert widget.item(0, 1).text() == "alice@example.com"
        assert widget.item(1, 0).text() == "Bob"
        assert widget.item(1, 1).text() == "bob@example.com"

    def test_load_rows_empty_list(self) -> None:
        """Handle empty rows list gracefully."""

        widget = PreviewTableWidget()
        widget.load_rows([])

        assert widget.rowCount() == 0

    def test_load_rows_none_values(
        self, sample_rows_with_none: list[dict[str, object]]
    ) -> None:
        """Convert None values to empty string."""

        widget = PreviewTableWidget()
        widget.load_rows(sample_rows_with_none)

        assert widget.item(0, 1).text() == ""

    def test_load_rows_resets_previous(
        self, sample_rows: list[dict[str, object]]
    ) -> None:
        """Loading new rows clears previous data."""

        widget = PreviewTableWidget()
        widget.load_rows(sample_rows)

        widget.load_rows([])

        assert widget.rowCount() == 0
