"""Tests for background review preview generation."""

from pathlib import Path

import pandas as pd

from report_convertor.components.review_worker import ReviewWorker
from report_convertor.components.template_editor import TemplateEditorWidget
from report_convertor.models.template import DestinationField, DraftMapping, SourceFile, TemplateDraft


def test_review_worker_emits_rows(qtbot, tmp_path: Path) -> None:
    """The worker should emit generated preview rows for a complete draft."""

    source_path = tmp_path / "source.xlsx"
    pd.DataFrame({"Name": ["Ada"]}).to_excel(source_path, index=False)
    draft = TemplateDraft(
        template_name="demo",
        destination_fields=[DestinationField(name="Employee Name")],
        sources=[SourceFile(key="source1", file_path=str(source_path))],
        mappings=[DraftMapping(destination_field="Employee Name", source_key="source1", source_column="Name")],
    )
    worker = ReviewWorker()

    with qtbot.waitSignal(worker.review_ready, timeout=1000) as blocker:
        worker.generate_review(1, draft, 5)

    assert blocker.args[0] == 1
    assert blocker.args[1] == [{"Employee Name": "Ada"}]


def test_review_worker_uses_completed_mappings_only(qtbot, tmp_path: Path) -> None:
    """The worker should still generate a review when only one field is mapped."""

    source_path = tmp_path / "source.xlsx"
    pd.DataFrame({"Name": ["Ada"], "Email": ["ada@example.com"]}).to_excel(source_path, index=False)
    draft = TemplateDraft(
        template_name="demo",
        destination_fields=[DestinationField(name="Employee Name"), DestinationField(name="Work Email")],
        sources=[SourceFile(key="source1", file_path=str(source_path))],
        mappings=[
            DraftMapping(destination_field="Employee Name", source_key="source1", source_column="Name"),
            DraftMapping(destination_field="Work Email"),
        ],
    )
    worker = ReviewWorker()

    with qtbot.waitSignal(worker.review_ready, timeout=1000) as blocker:
        worker.generate_review(2, draft, 5)

    assert blocker.args[0] == 2
    assert blocker.args[1] == [{"Employee Name": "Ada"}]


def test_template_editor_refreshes_review_on_mapping_change(qtbot, tmp_path: Path) -> None:
    """Mapping changes should regenerate the review preview section."""

    source_path = tmp_path / "source.xlsx"
    pd.DataFrame({"Name": ["Ada"], "Email": ["ada@example.com"]}).to_excel(source_path, index=False)
    draft = TemplateDraft(
        template_name="demo",
        destination_fields=[DestinationField(name="Employee Name"), DestinationField(name="Work Email")],
        sources=[SourceFile(key="source1", file_path=str(source_path))],
        mappings=[
            DraftMapping(destination_field="Employee Name"),
            DraftMapping(destination_field="Work Email"),
        ],
    )
    editor = TemplateEditorWidget(tmp_path, lambda _message: None)
    qtbot.addWidget(editor)
    editor.load_draft(draft)

    editor.mapping_editor.cellWidget(0, 1).setCurrentText("source1")
    editor.mapping_editor.cellWidget(0, 2).setCurrentText("Name")

    qtbot.waitUntil(lambda: editor.preview_table.rowCount() == 1, timeout=3000)
    assert editor.preview_table.item(0, 0).text() == "Ada"
