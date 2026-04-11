"""Tests for TemplateEditorController - template loading and source handling."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from report_convertor.components.template_editor_controller import (
    TemplateEditorController,
)
from report_convertor.models.template import TemplateDraft


class MockEditor:
    """Mock editor for testing controller."""

    def __init__(self):
        self.template_name_input = MagicMock()
        self.template_name_input.text.return_value = "test-template"
        self.template_path_input = MagicMock()
        self.template_path_input.text.return_value = ""
        self.source_from_s3_checkbox = MagicMock()
        self.source_from_s3_checkbox.isChecked.return_value = False
        self.sources = MagicMock()
        self.destination_fields = MagicMock()
        self.mapping_editor = MagicMock()
        self.summary_label = MagicMock()
        self.preview_rows_input = MagicMock()
        self.preview_rows_input.value.return_value = 10
        self.version_combo = MagicMock()
        self.templates_dir = Path("templates")
        self._show_status = MagicMock()

    def load_draft(self, draft):
        self._loaded_draft = draft

    @property
    def show_status(self):
        return self._show_status

    @show_status.setter
    def show_status(self, value):
        self._show_status = value

    def refresh_versions(self):
        pass


class TestBrowseTemplateSource:
    """Tests for browse_template_source method."""

    def test_browse_template_source_local_calls_load(self):
        """When 'Local File' selected, shows file dialog and loads."""
        editor = MockEditor()
        controller = TemplateEditorController(editor)

        with (
            patch.object(controller, "load_template") as mock_load,
            patch("PyQt6.QtWidgets.QInputDialog.getItem") as mock_dialog,
            patch("PyQt6.QtWidgets.QFileDialog.getOpenFileName") as mock_file,
        ):
            mock_dialog.return_value = ("Local File", True)
            mock_file.return_value = ("/path/to/template.json", True)
            controller.browse_template_source()

        mock_file.assert_called_once()
        mock_load.assert_called_once()

    def test_browse_template_source_s3_calls_unified_load(self):
        """When 'Amazon S3' selected, calls load_template_from_s3_unified."""
        editor = MockEditor()
        controller = TemplateEditorController(editor)

        with (
            patch.object(controller, "load_template_from_s3_unified") as mock_unified,
            patch("PyQt6.QtWidgets.QInputDialog.getItem") as mock_dialog,
        ):
            mock_dialog.return_value = ("Amazon S3", True)
            controller.browse_template_source()

        mock_unified.assert_called_once()

    def test_browse_template_source_cancelled(self):
        """When user cancels source selection, does nothing."""
        editor = MockEditor()
        controller = TemplateEditorController(editor)

        with (
            patch.object(controller, "load_template") as mock_load,
            patch.object(controller, "load_template_from_s3_unified") as mock_unified,
            patch("PyQt6.QtWidgets.QInputDialog.getItem") as mock_dialog,
        ):
            mock_dialog.return_value = ("", False)
            controller.browse_template_source()

        mock_load.assert_not_called()
        mock_unified.assert_not_called()


class TestLoadTemplateFromS3Unified:
    """Tests for load_template_from_s3_unified method."""

    @patch("boto3.client")
    def test_load_template_from_s3_unified_success(self, mock_boto):
        """Successfully loads template from S3 with version selection."""
        editor = MockEditor()
        controller = TemplateEditorController(editor)

        mock_s3_repo = MagicMock()
        mock_s3_repo.list_templates.return_value = ["template1", "template2"]
        mock_s3_repo.list_versions.side_effect = [
            ["v1", "v2"],
            ["v1"],
        ]
        mock_s3_repo.load_template.return_value = TemplateDraft(
            template_name="template1", output_file="output.xlsx"
        )
        controller._s3_repo = mock_s3_repo

        with (
            patch(
                "report_convertor.components.template_editor_controller.S3TemplateSelectDialog"
            ) as mock_dialog_class,
            patch.object(controller, "_run_action") as mock_run,
        ):
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = True
            mock_dialog.selected_template_version.return_value = ("template1", "v2")
            mock_dialog_class.return_value = mock_dialog

            def capture_action(action):
                action()

            mock_run.side_effect = capture_action

            controller.load_template_from_s3_unified()

        mock_s3_repo.load_template.assert_called_once_with("template1", "v2")

    @patch("boto3.client")
    def test_load_template_from_s3_unified_no_templates(self, mock_boto):
        """Raises error when no templates found."""
        editor = MockEditor()
        controller = TemplateEditorController(editor)

        mock_s3_repo = MagicMock()
        mock_s3_repo.list_templates.return_value = []
        controller._s3_repo = mock_s3_repo

        with (
            patch(
                "report_convertor.components.template_editor_controller.S3TemplateSelectDialog"
            ) as mock_dialog_class,
            patch.object(controller, "_run_action") as mock_run,
        ):
            mock_dialog = MagicMock()
            mock_dialog_class.return_value = mock_dialog

            def capture_action(action):
                with pytest.raises(ValueError, match="No templates found"):
                    action()

            mock_run.side_effect = capture_action

            controller.load_template_from_s3_unified()


class TestPushTemplateToS3:
    """Tests for push_template_to_s3 method."""

    @patch("boto3.client")
    def test_push_template_to_s3_prompts_for_name_if_empty(self, mock_boto):
        """Prompts for template name if name input is empty."""
        editor = MockEditor()
        editor.template_name_input.text.return_value = ""
        controller = TemplateEditorController(editor)

        mock_s3_repo = MagicMock()
        mock_s3_repo.list_versions.return_value = []
        controller._s3_repo = mock_s3_repo

        with (
            patch("PyQt6.QtWidgets.QInputDialog.getText") as mock_text,
            patch("PyQt6.QtWidgets.QMessageBox.question") as mock_msg,
            patch.object(controller, "_run_action") as mock_run,
        ):
            mock_text.return_value = ("new-template", True)
            mock_msg.return_value = 0x00004000  # Yes

            def capture_action(action):
                action()

            mock_run.side_effect = capture_action

            controller.push_template_to_s3()

        mock_s3_repo.save_template.assert_called_once()

    @patch("boto3.client")
    def test_push_template_to_s3_increments_version(self, mock_boto):
        """Automatically increments version when template exists."""
        editor = MockEditor()
        editor.template_name_input.text.return_value = "existing-template"
        controller = TemplateEditorController(editor)

        mock_s3_repo = MagicMock()
        mock_s3_repo.list_versions.return_value = ["v1", "v2"]
        controller._s3_repo = mock_s3_repo

        with (
            patch("PyQt6.QtWidgets.QMessageBox.question") as mock_msg,
            patch.object(controller, "_run_action") as mock_run,
            patch.object(controller, "_editor") as mock_editor,
        ):
            mock_msg.return_value = 0x00004000  # Yes

            def capture_action(action):
                action()

            mock_run.side_effect = capture_action

            controller.push_template_to_s3()

        call_args = mock_s3_repo.save_template.call_args
        assert call_args[1]["version"] == "v3"


class TestAddSourceFile:
    """Tests for add_source_file method."""

    def test_add_source_file_local_when_checkbox_unchecked(self):
        """Calls local file dialog when checkbox is unchecked."""
        editor = MockEditor()
        editor.source_from_s3_checkbox.isChecked.return_value = False
        controller = TemplateEditorController(editor)

        with patch.object(controller, "_add_source_from_local") as mock_local:
            controller.add_source_file()
            mock_local.assert_called_once()

    def test_add_source_file_s3_when_checkbox_checked(self):
        """Calls S3 dialog when checkbox is checked."""
        editor = MockEditor()
        editor.source_from_s3_checkbox.isChecked.return_value = True
        controller = TemplateEditorController(editor)

        with patch.object(controller, "_add_source_from_s3") as mock_s3:
            controller.add_source_file()
            mock_s3.assert_called_once()


class TestAddSourceFromS3:
    """Tests for _add_source_from_s3 method."""

    @patch("boto3.client")
    def test_add_source_from_s3_success(self, mock_boto):
        """Successfully adds source from S3."""
        editor = MockEditor()
        controller = TemplateEditorController(editor)

        mock_report_repo = MagicMock()
        mock_report_repo.list_reports.return_value = ["report1.xlsx", "report2.xlsx"]
        mock_report_repo.download_report.return_value = Path("/cache/report1.xlsx")
        controller._s3_report_repo = mock_report_repo

        editor.sources.add_source = MagicMock()
        controller._reader = MagicMock()

        with (
            patch("PyQt6.QtWidgets.QInputDialog.getItem") as mock_dialog,
            patch.object(controller, "_run_action") as mock_run,
            patch.object(controller, "_append_source"),
        ):
            mock_dialog.return_value = ("report1.xlsx", True)

            def capture_action(action):
                action()

            mock_run.side_effect = capture_action

            controller._add_source_from_s3()

        mock_report_repo.download_report.assert_called_once_with("report1.xlsx")

    @patch("boto3.client")
    def test_add_source_from_s3_no_reports(self, mock_boto):
        """Raises error when no reports found."""
        editor = MockEditor()
        controller = TemplateEditorController(editor)

        mock_report_repo = MagicMock()
        mock_report_repo.list_reports.return_value = []
        controller._s3_report_repo = mock_report_repo

        with (
            patch("PyQt6.QtWidgets.QInputDialog.getItem") as mock_dialog,
            patch.object(controller, "_run_action") as mock_run,
        ):
            mock_dialog.return_value = ("", False)

            def capture_action(action):
                with pytest.raises(ValueError, match="No reports found"):
                    action()

            mock_run.side_effect = capture_action

            controller._add_source_from_s3()
