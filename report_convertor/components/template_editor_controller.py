"""Controller for template editor actions."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from report_convertor.features.mapping.preview_service import PreviewService
from report_convertor.features.reports.generator import ReportGenerator
from report_convertor.features.sources.workbook_reader import WorkbookReader
from report_convertor.features.templates.service import TemplateService
from report_convertor.models.template import TemplateDraft


class TemplateEditorController:
    """Handle user actions for the template editor widget."""

    def __init__(self, editor) -> None:
        self._editor = editor
        self._service = TemplateService()
        self._preview = PreviewService()
        self._generator = ReportGenerator()
        self._reader = WorkbookReader()

    def new_draft(self) -> None:
        self._editor.load_draft(TemplateDraft(template_name="draft-template", output_file="output.xlsx"))
        self._editor.template_name_input.clear()
        self._editor.template_path_input.clear()
        self._editor.summary_label.setText(self._editor.summary())
        self._editor.show_status("Started a new template draft.")

    def browse_template(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(self._editor, "Select Template", str(self._editor.templates_dir), "JSON Files (*.json)")
        if selected:
            self._editor.template_path_input.setText(selected)

    def load_template(self) -> None:
        self._run_action(
            lambda: self._editor.load_draft(
                self._service.load_template(self._editor.template_path_input.text().strip(), self._editor.templates_dir),
            ),
            "Template loaded.",
            require_path=True,
        )

    def add_destination_field(self) -> None:
        name, accepted = QInputDialog.getText(self._editor, "Add Destination Field", "Field name")
        if accepted and name.strip():
            if name.strip() in self._editor.destination_fields.field_names():
                self._error(f"Destination field '{name.strip()}' already exists.")
                return
            self._editor.destination_fields.add_field(name.strip())
            self._editor.sync_editor()

    def import_destination_fields(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(self._editor, "Select Report File", str(Path.cwd()), "Excel Files (*.xlsx *.xls)")
        if selected:
            self._run_action(lambda: self._editor.merge_imported_fields(self._service.import_destination_fields(selected)), "Destination headers imported.")

    def remove_destination_field(self) -> None:
        if self._editor.destination_fields.remove_selected():
            self._editor.sync_editor()

    def add_source_file(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(self._editor, "Select Source Report", str(Path.cwd()), "Excel Files (*.xlsx *.xls)")
        if selected:
            self._run_action(lambda: self._append_source(selected), "Source report added.")

    def remove_source_file(self) -> None:
        removed = self._editor.sources.remove_selected()
        if removed:
            self._editor.source_columns.pop(removed.key, None)
            self._editor.mapping_editor.clear_source(removed.key)
            self._editor.sync_editor()

    def save_template(self) -> None:
        def action() -> None:
            draft = self._editor.compose_draft(require_name=True)
            destination = self._service.save_template(draft, self._editor.templates_dir)
            self._editor.template_path_input.setText(str(destination))
            self._editor.summary_label.setText(self._editor.summary())
            self._editor.show_status(f"Saved template: {destination.name}")

        self._run_action(action)

    def preview_template(self) -> None:
        def action() -> None:
            rows = self._preview.preview_rows(self._editor.compose_draft(require_name=False), row_count=self._editor.preview_rows_input.value())
            self._editor.preview_table.load_rows(rows)
            self._editor.show_status(f"Loaded {len(rows)} preview rows.")

        self._run_action(action)

    def generate_report(self) -> None:
        def action() -> None:
            output = self._generator.export(self._editor.compose_draft(require_name=True))
            QMessageBox.information(self._editor, "Report Generated", f"Saved report to:\n{output}")
            self._editor.show_status(f"Report generated: {output}")

        self._run_action(action)

    def _append_source(self, file_path: str) -> None:
        source = self._service.create_source(file_path, {item.key for item in self._editor.sources.sources()})
        self._reader.list_columns(source)
        self._editor.sources.add_source(source)
        self._editor.refresh_source_columns(self._reader)
        self._editor.sync_editor()

    def _run_action(self, action, success_message: str | None = None, require_path: bool = False) -> None:
        try:
            if require_path and not self._editor.template_path_input.text().strip():
                raise ValueError("Choose a template file or enter a template name.")
            action()
            if success_message:
                self._editor.show_status(success_message)
        except (FileNotFoundError, ValueError, OSError) as error:
            self._error(str(error))

    def _error(self, message: str) -> None:
        self._editor.show_status(message)
        QMessageBox.critical(self._editor, "Error", message)
