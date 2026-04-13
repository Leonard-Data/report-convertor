"""Tests for S3TemplateSelectDialog component."""

import pytest

from report_convertor.components.s3_template_select_dialog import S3TemplateSelectDialog


class TestS3TemplateSelectDialog:
    """Test suite for S3TemplateSelectDialog."""

    def test_selected_template_version_returns_none_initially(self, qtbot) -> None:
        """No selection returns None initially."""
        items = [{"name": "template1", "versions": ["v1", "v2"]}]

        dialog = S3TemplateSelectDialog(None, items)
        qtbot.addWidget(dialog)

        assert dialog.selected_template_version() is None

    def test_selected_version_after_ok_click(self, qtbot) -> None:
        """Selecting version and clicking OK returns correct tuple."""
        items = [{"name": "template1", "versions": ["v1", "v2"]}]

        dialog = S3TemplateSelectDialog(None, items)
        qtbot.addWidget(dialog)

        parent = dialog._tree.topLevelItem(0)
        version_item = parent.child(1)

        dialog._tree.setCurrentItem(version_item)
        dialog._on_ok_clicked()

        result = dialog.selected_template_version()
        assert result == ("template1", "v2")

    def test_selected_version_first_version_when_parent_clicked(self, qtbot) -> None:
        """Clicking parent template auto-selects first version."""
        items = [{"name": "template1", "versions": ["v1", "v2"]}]

        dialog = S3TemplateSelectDialog(None, items)
        qtbot.addWidget(dialog)

        parent = dialog._tree.topLevelItem(0)

        dialog._tree.setCurrentItem(parent)
        dialog._on_ok_clicked()

        result = dialog.selected_template_version()
        assert result == ("template1", "v1")

    def test_search_filters_templates(self, qtbot) -> None:
        """Search input filters displayed templates."""
        items = [
            {"name": "template-alpha", "versions": ["v1"]},
            {"name": "template-beta", "versions": ["v1"]},
        ]

        dialog = S3TemplateSelectDialog(None, items)
        qtbot.addWidget(dialog)

        dialog._search_input.setText("alpha")

        assert dialog._tree.topLevelItemCount() == 1
        assert dialog._tree.topLevelItem(0).text(0) == "template-alpha"

    def test_parent_template_has_all_versions(self, qtbot) -> None:
        """Parent template shows all its versions as children."""
        items = [{"name": "template1", "versions": ["v1", "v2", "v3"]}]

        dialog = S3TemplateSelectDialog(None, items)
        qtbot.addWidget(dialog)

        parent = dialog._tree.topLevelItem(0)
        assert parent.childCount() == 3

    def test_no_templates_handled(self, qtbot) -> None:
        """Empty template list handled gracefully."""
        dialog = S3TemplateSelectDialog(None, [])
        qtbot.addWidget(dialog)

        assert dialog._tree.topLevelItemCount() == 0
        assert dialog.selected_template_version() is None

    def test_version_displayed_in_tree(self, qtbot) -> None:
        """Version strings are displayed as children."""
        items = [{"name": "my-template", "versions": ["version-1.0", "version-2.0"]}]

        dialog = S3TemplateSelectDialog(None, items)
        qtbot.addWidget(dialog)

        parent = dialog._tree.topLevelItem(0)
        assert parent.text(0) == "my-template"
        assert parent.child(0).text(0) == "version-1.0"
        assert parent.child(1).text(0) == "version-2.0"
