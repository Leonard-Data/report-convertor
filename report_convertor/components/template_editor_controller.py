"""Controller for template editor actions."""

from __future__ import annotations

from pathlib import Path
import os

from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from report_convertor.components.s3_source_select_dialog import S3SourceSelectDialog
from report_convertor.components.s3_template_select_dialog import S3TemplateSelectDialog
from report_convertor.features.mapping.preview_service import PreviewService
from report_convertor.features.reports.generator import ReportGenerator
from report_convertor.features.reports.s3_uploader import S3Uploader
from report_convertor.features.sources.workbook_reader import WorkbookReader
from report_convertor.features.storage.s3_report_repository import S3ReportRepository
from report_convertor.features.templates.service import TemplateService
from report_convertor.features.templates.s3_repository import S3TemplateRepository
from report_convertor.models.template import TemplateDraft


class TemplateEditorController:
    """Handle user actions for the template editor widget."""

    def __init__(self, editor) -> None:
        self._editor = editor
        self._service = TemplateService()
        self._preview = PreviewService()
        self._generator = ReportGenerator()
        self._reader = WorkbookReader()
        self._s3_repo = S3TemplateRepository()
        self._s3_uploader = S3Uploader()
        self._s3_report_repo = S3ReportRepository()

    def new_draft(self) -> None:
        self._editor.load_draft(
            TemplateDraft(template_name="draft-template", output_file="output.xlsx")
        )
        self._editor.template_name_input.clear()
        self._editor.template_path_input.clear()
        self._editor.summary_label.setText(self._editor.summary())
        self._editor.show_status("Started a new template draft.")

    def browse_template_source(self) -> None:
        source, ok = QInputDialog.getItem(
            self._editor,
            "Select Template Source",
            "Choose where to load template from:",
            ["Local File", "Amazon S3"],
            0,
            False,
        )
        if not ok:
            return

        if source == "Local File":
            selected, _ = QFileDialog.getOpenFileName(
                self._editor,
                "Select Template",
                str(self._editor.templates_dir),
                "JSON Files (*.json)",
            )
            if selected:
                self._editor.template_path_input.setText(selected)
                self.load_template()
        else:
            self.load_template_from_s3_unified()

    def load_template_from_s3_unified(self) -> None:
        def action() -> None:
            templates = self._s3_repo.list_templates()
            if not templates:
                raise ValueError("No templates found in S3")

            items = []
            for name in templates:
                versions = self._s3_repo.list_versions(name)
                items.append({"name": name, "versions": versions})

            dialog = S3TemplateSelectDialog(self._editor, items)
            if dialog.exec():
                selected = dialog.selected_template_version()
                if selected:
                    name, version = selected
                    draft = self._s3_repo.load_template(name, version)

                    for source in draft.sources:
                        if source.file_path:
                            source_path = Path(source.file_path)
                            if source_path.exists():
                                pass
                            elif (
                                "/" in source.file_path
                                or "\\" in source.file_path
                                or source.file_path.startswith("s3://")
                            ):
                                try:
                                    local_path = (
                                        self._s3_report_repo.download_report_by_key(
                                            source.file_path
                                        )
                                    )
                                    source.file_path = str(local_path)
                                except FileNotFoundError:
                                    self._editor.show_status(
                                        f"Warning: Source not found in S3: {source.file_path}"
                                    )

                    self._editor.load_draft(draft)
                    self._editor.template_path_input.setText(f"s3://{name}_{version}")
                    self._editor.refresh_versions()
                    self._editor.show_status(f"Loaded template: {name} ({version})")

        self._run_action(action)

    def push_template_to_s3(self) -> None:
        def action() -> None:
            name = self._editor.template_name_input.text().strip()
            if not name:
                name, ok = QInputDialog.getText(
                    self._editor, "Template Name", "Enter template name:"
                )
                if not ok or not name.strip():
                    return
                self._editor.template_name_input.setText(name.strip())
                name = name.strip()

            current_versions = self._s3_repo.list_versions(name)
            existing_nums = []
            for v in current_versions:
                if v.startswith("0.0.0."):
                    try:
                        existing_nums.append(int(v.split(".")[-1]))
                    except (ValueError, IndexError):
                        pass
            next_num = max(existing_nums, default=0) + 1
            next_version = f"0.0.0.{next_num}"

            confirm = QMessageBox.question(
                self._editor,
                "Confirm Push to S3",
                f"Push '{name}' as version '{next_version}' to S3?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

            draft = self._editor.compose_draft(require_name=True)
            key = self._s3_repo.save_template(draft, version=next_version)
            self._editor.refresh_versions()
            self._editor.template_path_input.setText(f"s3://{name}_{next_version}")
            self._editor.show_status(f"Pushed to S3: {name} ({next_version})")

        self._run_action(action)

    def browse_template(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self._editor,
            "Select Template",
            str(self._editor.templates_dir),
            "JSON Files (*.json)",
        )
        if selected:
            self._editor.template_path_input.setText(selected)

    def load_template(self) -> None:
        self._run_action(
            lambda: self._editor.load_draft(
                self._service.load_template(
                    self._editor.template_path_input.text().strip(),
                    self._editor.templates_dir,
                ),
            ),
            "Template loaded.",
            require_path=True,
        )

    def add_destination_field(self) -> None:
        name, accepted = QInputDialog.getText(
            self._editor, "Add Destination Field", "Field name"
        )
        if accepted and name.strip():
            if name.strip() in self._editor.destination_fields.field_names():
                self._error(f"Destination field '{name.strip()}' already exists.")
                return
            self._editor.destination_fields.add_field(name.strip())
            self._editor.sync_editor()

    def import_destination_fields(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self._editor,
            "Select Report File",
            str(Path.cwd()),
            "Excel Files (*.xlsx *.xls)",
        )
        if selected:
            self._run_action(
                lambda: self._editor.merge_imported_fields(
                    self._service.import_destination_fields(selected)
                ),
                "Destination headers imported.",
            )

    def remove_destination_field(self) -> None:
        if self._editor.destination_fields.remove_selected():
            self._editor.sync_editor()

    def add_source_file(self) -> None:
        if self._editor.source_from_s3_checkbox.isChecked():
            self._add_source_from_s3()
        else:
            self._add_source_from_local()

    def _add_source_from_s3(self) -> None:
        def action() -> None:
            items = self._s3_report_repo.list_reports_with_folders()
            if not items:
                raise ValueError("No reports found in S3")

            dialog = S3SourceSelectDialog(self._editor, items)
            if dialog.exec():
                selected = dialog.selected_files()
                if not selected:
                    return
                for folder, file, key in selected:
                    local_path = self._s3_report_repo.download_report(key)
                    self._append_source(str(local_path))
                self._editor.show_status(f"Loaded {len(selected)} report(s) from S3")

        self._run_action(action)

    def _add_source_from_local(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self._editor,
            "Select Source Report",
            str(Path.cwd()),
            "Excel Files (*.xlsx *.xls)",
        )
        if selected:
            self._run_action(
                lambda: self._append_source(selected), "Source report added."
            )

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

    def save_template_to_s3(self) -> None:
        def action() -> None:
            draft = self._editor.compose_draft(require_name=True)
            key = self._s3_repo.save_template(draft)
            self._editor.template_path_input.setText(key)
            self._editor.summary_label.setText(self._editor.summary())
            self._editor.show_status(f"Saved template to S3: {key}")

        self._run_action(action)

    def load_template_from_s3(self) -> None:
        def action() -> None:
            names = self._s3_repo.list_templates()
            if not names:
                raise ValueError("No templates found in S3")
            name, accepted = QInputDialog.getItem(
                self._editor, "Load from S3", "Select template:", names, 0, False
            )
            if accepted:
                draft = self._s3_repo.load_template(name)
                self._editor.load_draft(draft)
                self._editor.template_path_input.setText(f"s3://{name}")
                self._editor.show_status(f"Loaded template from S3: {name}")

        self._run_action(action)

    def list_s3_versions(self) -> list[str]:
        """List available versions for the current template."""
        name = self._editor.template_name_input.text().strip()
        if not name:
            return []
        try:
            return self._s3_repo.list_versions(name)
        except Exception:
            return []

    def preview_template(self) -> None:
        def action() -> None:
            rows = self._preview.preview_rows(
                self._editor.compose_draft(require_name=False),
                row_count=self._editor.preview_rows_input.value(),
            )
            self._editor.preview_table.load_rows(rows)
            self._editor.show_status(f"Loaded {len(rows)} preview rows.")

        self._run_action(action)

    def generate_report(self) -> None:
        def action() -> None:
            output = self._generator.export(
                self._editor.compose_draft(require_name=True)
            )

            msg_box = QMessageBox(self._editor)
            msg_box.setWindowTitle("Report Generated")
            msg_box.setText(f"Report saved to:\n{output}")
            open_btn = msg_box.addButton("Open File", QMessageBox.ButtonRole.ActionRole)
            ok_btn = msg_box.addButton(QMessageBox.StandardButton.Ok)
            msg_box.setDefaultButton(ok_btn)
            msg_box.exec()

            if msg_box.clickedButton() == open_btn:
                output_path = Path(output)
                if output_path.exists():
                    os.startfile(output_path) if os.name == "nt" else None

            self._editor.show_status(f"Report generated: {output}")

        self._run_action(action)

    def generate_and_upload(self) -> None:
        def action() -> None:
            draft = self._editor.compose_draft(require_name=True)
            output = self._generator.export(draft)
            result = self._s3_uploader.upload(output)

            msg_box = QMessageBox(self._editor)
            msg_box.setWindowTitle("Report Uploaded")
            msg_box.setText(f"Local: {output}\nS3: {result['key']}")
            open_btn = msg_box.addButton("Open File", QMessageBox.ButtonRole.ActionRole)
            ok_btn = msg_box.addButton(QMessageBox.StandardButton.Ok)
            msg_box.setDefaultButton(ok_btn)
            msg_box.exec()

            if msg_box.clickedButton() == open_btn:
                output_path = Path(output)
                if output_path.exists():
                    os.startfile(output_path) if os.name == "nt" else None

            self._editor.show_status(f"Report generated and uploaded: {result['key']}")

        self._run_action(action)

    def _append_source(self, file_path: str) -> None:
        source = self._service.create_source(
            file_path, {item.key for item in self._editor.sources.sources()}
        )
        self._reader.list_columns(source)
        self._editor.sources.add_source(source)
        self._editor.refresh_source_columns(self._reader)
        self._editor.sync_editor()

    def _run_action(
        self, action, success_message: str | None = None, require_path: bool = False
    ) -> None:
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
