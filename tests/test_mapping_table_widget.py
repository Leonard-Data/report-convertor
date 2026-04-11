"""Tests for EditableMappingTableWidget component."""

import pytest

from report_convertor.components.editable_mapping_table import EditableMappingTableWidget
from report_convertor.models.template import TemplateDraft


class TestMappingTableWidget:
    """Test suite for the editable mapping table."""

    def test_load_template_populates_rows(
        self, sample_template: TemplateDraft
    ) -> None:
        """Verify draft mappings are loaded into table rows."""

        widget = EditableMappingTableWidget()
        widget.load_draft(sample_template.ensure_mapping_rows(), {"source1": ["Name", "Email"]})

        assert widget.rowCount() == 2
        assert widget.item(0, 0).text() == "Employee Name"
        assert widget.item(1, 0).text() == "Work Email"

    def test_load_template_correct_columns(
        self, sample_template: TemplateDraft
    ) -> None:
        """Verify correct mapping values for each draft row."""

        widget = EditableMappingTableWidget()
        widget.load_draft(sample_template.ensure_mapping_rows(), {"source1": ["Name", "Email"]})

        row_0 = widget.item(0, 0).text()
        row_1 = widget.item(1, 0).text()

        assert row_0 == "Employee Name"
        assert row_1 == "Work Email"

    def test_load_template_source_key_column(
        self, sample_template: TemplateDraft
    ) -> None:
        """Verify source key is available in the combo box column."""

        widget = EditableMappingTableWidget()
        widget.load_draft(sample_template.ensure_mapping_rows(), {"source1": ["Name", "Email"]})

        assert widget.cellWidget(0, 1).currentText() == "source1"
        assert widget.cellWidget(1, 1).currentText() == "source1"

    def test_load_template_source_column(
        self, sample_template: TemplateDraft
    ) -> None:
        """Verify source column is displayed in searchable combo boxes."""

        widget = EditableMappingTableWidget()
        widget.load_draft(sample_template.ensure_mapping_rows(), {"source1": ["Name", "Email"]})

        assert widget.cellWidget(0, 2).currentText() == "Name"
        assert widget.cellWidget(1, 2).currentText() == "Email"

    def test_load_template_resets_previous(
        self,
        sample_template: TemplateDraft,
        sample_template_single_mapping: TemplateDraft,
    ) -> None:
        """Loading a new draft clears previous rows."""

        widget = EditableMappingTableWidget()
        widget.load_draft(sample_template.ensure_mapping_rows(), {"source1": ["Name", "Email"]})

        widget.load_draft(sample_template_single_mapping.ensure_mapping_rows(), {"source1": ["Name"]})

        assert widget.rowCount() == 1

    def test_horizontal_headers(self, sample_template: TemplateDraft) -> None:
        """Verify horizontal header labels."""

        widget = EditableMappingTableWidget()
        widget.load_draft(sample_template.ensure_mapping_rows(), {"source1": ["Name", "Email"]})

        assert widget.horizontalHeaderItem(0).text() == "Destination Field"
        assert widget.horizontalHeaderItem(1).text() == "Source File"
        assert widget.horizontalHeaderItem(2).text() == "Source Column"

    def test_mapping_changed_signal_emits(self, qtbot, sample_template: TemplateDraft) -> None:
        """Changing a mapping should emit the mapping-changed signal."""

        widget = EditableMappingTableWidget()
        qtbot.addWidget(widget)
        widget.load_draft(sample_template.ensure_mapping_rows(), {"source1": ["Name", "Email"]})

        with qtbot.waitSignal(widget.mapping_changed, timeout=1000):
            widget.cellWidget(0, 2).setCurrentText("Email")
