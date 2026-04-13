"""Template authoring widget for local template workflows."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, QTimer, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from report_convertor.components.destination_fields_list import DestinationFieldsWidget
from report_convertor.components.editable_mapping_table import (
    EditableMappingTableWidget,
)
from report_convertor.components.mapping_table import PreviewTableWidget
from report_convertor.components.review_worker import ReviewWorker
from report_convertor.components.source_files_list import SourceFilesWidget
from report_convertor.components.template_editor_controller import (
    TemplateEditorController,
)
from report_convertor.components.template_editor_support import (
    merge_destination_names,
    normalize_mappings,
    refresh_source_columns,
    summary_text,
)
from report_convertor.features.sources.workbook_reader import WorkbookReader
from report_convertor.models.template import DestinationField, TemplateDraft


class TemplateEditorWidget(QWidget):
    """Create, save, preview, and generate reports from template drafts."""

    request_review = pyqtSignal(int, object, int)

    def __init__(self, templates_dir: Path, status_callback) -> None:
        super().__init__()
        self.templates_dir = templates_dir
        self.show_status = status_callback
        self.source_columns: dict[str, list[str]] = {}
        self._review_request_id = 0
        self.template_path_input = QLineEdit()
        self.template_name_input = QLineEdit()
        self.version_combo = QComboBox()
        self.version_combo.setEditable(False)
        self.output_file_input = QLineEdit("output.xlsx")
        self.preview_rows_input = QSpinBox()
        self.summary_label = QLabel(
            "Create a template draft, save it, then preview or generate a report."
        )
        self.destination_fields = DestinationFieldsWidget()
        self.sources = SourceFilesWidget()
        self.source_from_s3_checkbox = QCheckBox("From S3")
        self.source_from_s3_checkbox.setToolTip("Load source reports from S3")
        self.mapping_editor = EditableMappingTableWidget()
        self.preview_table = PreviewTableWidget()
        self._preview_container = QWidget()
        self._controller = TemplateEditorController(self)
        self._review_timer = QTimer(self)
        self._review_timer.setSingleShot(True)
        self._review_timer.timeout.connect(self._dispatch_review_request)
        self._review_thread = QThread(self)
        self._review_worker = ReviewWorker()
        self._review_worker.moveToThread(self._review_thread)
        self.request_review.connect(
            self._review_worker.generate_review, Qt.ConnectionType.QueuedConnection
        )
        self._review_worker.review_ready.connect(self._handle_review_ready)
        self._review_worker.review_failed.connect(self._handle_review_failed)
        self._review_thread.start()
        self.destroyed.connect(lambda *_args: self._stop_review_thread())
        self._build_ui()
        self.load_draft(
            TemplateDraft(template_name="draft-template", output_file="output.xlsx")
        )
        self.template_name_input.clear()
        self.mapping_editor.mapping_changed.connect(self.schedule_review_refresh)
        self.preview_rows_input.valueChanged.connect(self.schedule_review_refresh)
        self.source_from_s3_checkbox.toggled.connect(self._on_source_s3_toggled)

    def _build_ui(self) -> None:
        self.preview_rows_input.setRange(1, 1000)
        self.preview_rows_input.setValue(10)
        form = QFormLayout()
        form.addRow("Template File", self._file_row())
        form.addRow("Template Name", self.template_name_input)
        form.addRow("Version", self.version_combo)
        form.addRow("Output File", self.output_file_input)
        top = QHBoxLayout()
        top.addLayout(
            self._panel(
                "Destination Fields",
                self.destination_fields,
                [
                    ("Add Field", self._controller.add_destination_field),
                    ("Import Headers", self._controller.import_destination_fields),
                    ("Remove Field", self._controller.remove_destination_field),
                ],
            ),
            1,
        )
        top.addLayout(
            self._panel(
                "Source Reports",
                self.sources,
                [
                    ("Add Source", self._controller.add_source_file),
                    ("Remove Source", self._controller.remove_source_file),
                ],
                header_widget=self.source_from_s3_checkbox,
            ),
            1,
        )
        actions = QHBoxLayout()
        actions.addWidget(QLabel("Preview Rows"))
        actions.addWidget(self.preview_rows_input)
        actions.addStretch(1)
        for text, handler in [
            ("Clear", self._controller.clear_draft),
            ("Save Template", self._controller.save_template),
            ("Push to S3", self._controller.push_template_to_s3),
            ("Preview", self._controller.preview_template),
            ("Generate Report", self._controller.generate_report),
        ]:
            button = QPushButton(text)
            button.clicked.connect(handler)
            actions.addWidget(button)
        layout = QVBoxLayout()
        for item in [
            form,
            self.summary_label,
            top,
            QLabel("Mappings"),
            self.mapping_editor,
            actions,
        ]:
            layout.addLayout(item) if isinstance(
                item, (QFormLayout, QHBoxLayout)
            ) else layout.addWidget(item)

        self._build_preview_container()
        layout.addWidget(self._preview_container)
        self.setLayout(layout)

    def _file_row(self) -> QWidget:
        return self._button_row(
            self.template_path_input,
            [
                ("Browse", self._controller.browse_template_source),
                ("Load", self._controller.load_template),
            ],
        )

    def _panel(
        self,
        title: str,
        widget: QWidget,
        buttons: list[tuple[str, object]],
        header_widget: QWidget | None = None,
    ) -> QVBoxLayout:
        layout = QVBoxLayout()
        header = QHBoxLayout()
        header.addWidget(QLabel(title))
        if header_widget:
            header.addWidget(header_widget)
        header.addStretch()
        layout.addLayout(header)
        layout.addWidget(widget)
        layout.addWidget(self._button_row(None, buttons))
        return layout

    def _button_row(
        self, first_widget: QWidget | None, buttons: list[tuple[str, object]]
    ) -> QWidget:
        row, layout = QWidget(), QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        if first_widget is not None:
            layout.addWidget(first_widget)
        for text, handler in buttons:
            button = QPushButton(text)
            button.clicked.connect(handler)
            layout.addWidget(button)
        row.setLayout(layout)
        return row

    def _build_preview_container(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Preview"))
        layout.addWidget(self.preview_table)
        self._preview_container.setLayout(layout)

    def show_preview_in_main(self, show: bool) -> None:
        if show:
            if self._preview_container.parent() != self:
                self._preview_container.setParent(self)
                layout = self.layout()
                if layout is not None:
                    layout.addWidget(self._preview_container)
        else:
            if self._preview_container.parent() == self:
                self._preview_container.setParent(None)

    @property
    def preview_container(self) -> QWidget:
        return self._preview_container

    def load_draft(self, draft: TemplateDraft) -> None:
        draft = draft.ensure_mapping_rows()
        self.template_name_input.setText(draft.template_name)
        self.output_file_input.setText(draft.output_file)
        self.destination_fields.load_fields(
            [field.name for field in draft.destination_fields]
        )
        self.sources.load_sources(
            draft.sources, self.source_from_s3_checkbox.isChecked()
        )
        self.refresh_source_columns(WorkbookReader())
        self.mapping_editor.load_draft(draft, self.source_columns)
        self.preview_table.load_rows([])
        self.summary_label.setText(self.summary())
        self.schedule_review_refresh()

    def compose_draft(self, require_name: bool) -> TemplateDraft:
        name = self.template_name_input.text().strip()
        if require_name and not name:
            raise ValueError("Template name is required. Please enter a name before generating.")
        name = name or "draft-template"
        names = self.destination_fields.field_names()
        sources = self.sources.sources()
        mappings = normalize_mappings(
            self.mapping_editor.read_mappings(), names, sources
        )
        return TemplateDraft(
            template_name=name,
            output_file=self.output_file_input.text().strip() or "output.xlsx",
            destination_fields=[DestinationField(name=name) for name in names],
            sources=sources,
            mappings=mappings,
        ).ensure_mapping_rows()

    def merge_imported_fields(self, imported_fields) -> None:
        names = self.destination_fields.field_names()
        self.destination_fields.load_fields(
            merge_destination_names(names, [field.name for field in imported_fields])
        )
        self.sync_editor()

    def refresh_versions(self) -> None:
        """Reload version dropdown from S3 for current template."""
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        versions = self._controller.list_s3_versions()
        for version in versions:
            self.version_combo.addItem(version)
        self.version_combo.blockSignals(False)

    def refresh_source_columns(self, reader: WorkbookReader) -> None:
        self.source_columns = refresh_source_columns(reader, self.sources.sources())

    def sync_editor(self) -> None:
        draft = self.compose_draft(require_name=False)
        self.mapping_editor.load_draft(draft, self.source_columns)
        self.summary_label.setText(self.summary())
        self.schedule_review_refresh()

    def summary(self) -> str:
        return summary_text(
            self.template_name_input.text().strip(),
            self.compose_draft(require_name=False),
        )

    def schedule_review_refresh(self) -> None:
        """Debounce background review refresh while the user edits mappings."""

        self._review_timer.start(250)

    @pyqtSlot()
    def _dispatch_review_request(self) -> None:
        draft = self.compose_draft(require_name=False)
        if sum(1 for mapping in draft.mappings if mapping.is_complete) < 1:
            self.preview_table.load_rows([])
            self.show_status(
                "Review preview will appear after at least one field is mapped."
            )
            return
        self._review_request_id += 1
        self.show_status("Refreshing review preview...")
        self.request_review.emit(
            self._review_request_id, draft, self.preview_rows_input.value()
        )

    @pyqtSlot(int, list)
    def _handle_review_ready(
        self, request_id: int, rows: list[dict[str, object]]
    ) -> None:
        if request_id != self._review_request_id:
            return
        self.preview_table.load_rows(rows)
        self.show_status(f"Review preview refreshed with {len(rows)} row(s).")

    @pyqtSlot(int, str)
    def _handle_review_failed(self, request_id: int, message: str) -> None:
        if request_id != self._review_request_id:
            return
        self.preview_table.load_rows([])
        self.show_status(message)

    def closeEvent(self, event) -> None:
        self._stop_review_thread()
        super().closeEvent(event)

    @pyqtSlot()
    def _on_source_s3_toggled(self) -> None:
        self.sources.set_from_s3(self.source_from_s3_checkbox.isChecked())

    def _stop_review_thread(self) -> None:
        if self._review_thread.isRunning():
            self._review_thread.quit()
            self._review_thread.wait()
