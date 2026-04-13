"""Tests for preview and report export services."""

from pathlib import Path

import pandas as pd
import pytest

from report_convertor.features.mapping.preview_service import PreviewService
from report_convertor.features.reports.generator import ReportGenerator
from report_convertor.models.template import (
    DestinationField,
    DraftMapping,
    SourceFile,
    TemplateDraft,
)


def test_generator_exports_expected_columns(tmp_path: Path) -> None:
    """The generator should map columns into a new workbook."""

    source_path = tmp_path / "source.xlsx"
    output_path = tmp_path / "report.xlsx"

    pd.DataFrame(
        {"Name": ["Ada", "Grace"], "Email": ["a@example.com", "g@example.com"]}
    ).to_excel(
        source_path,
        index=False,
    )

    template = TemplateDraft(
        template_name="demo-template",
        output_file=str(output_path),
        destination_fields=[
            DestinationField(name="Employee Name"),
            DestinationField(name="Work Email"),
        ],
        sources=[SourceFile(key="source1", file_path=str(source_path))],
        mappings=[
            DraftMapping(
                destination_field="Employee Name",
                source_key="source1",
                source_column="Name",
            ),
            DraftMapping(
                destination_field="Work Email",
                source_key="source1",
                source_column="Email",
            ),
        ],
    )

    preview_rows = PreviewService().preview_rows(template, row_count=1)
    generated_path = ReportGenerator().export(template)
    generated_frame = pd.read_excel(generated_path)

    assert preview_rows == [{"Employee Name": "Ada", "Work Email": "a@example.com"}]
    assert generated_path == output_path
    assert list(generated_frame.columns) == ["Employee Name", "Work Email"]
    assert generated_frame.iloc[1].to_dict() == {
        "Employee Name": "Grace",
        "Work Email": "g@example.com",
    }


def test_preview_allows_partially_mapped_drafts(tmp_path: Path) -> None:
    """Review preview should use completed mappings only."""

    source_path = tmp_path / "source.xlsx"
    pd.DataFrame({"Name": ["Ada"], "Email": ["ada@example.com"]}).to_excel(
        source_path, index=False
    )
    template = TemplateDraft(
        template_name="demo-template",
        destination_fields=[
            DestinationField(name="Employee Name"),
            DestinationField(name="Work Email"),
        ],
        sources=[SourceFile(key="source1", file_path=str(source_path))],
        mappings=[
            DraftMapping(
                destination_field="Employee Name",
                source_key="source1",
                source_column="Name",
            ),
            DraftMapping(destination_field="Work Email"),
        ],
    )

    assert PreviewService().preview_rows(template) == [{"Employee Name": "Ada"}]


def test_export_stays_strict_for_incomplete_drafts(tmp_path: Path) -> None:
    """Final report generation allows incomplete mappings with empty columns."""

    source_path = tmp_path / "source.xlsx"
    pd.DataFrame({"Name": ["Ada"]}).to_excel(source_path, index=False)
    template = TemplateDraft(
        template_name="demo-template",
        destination_fields=[
            DestinationField(name="Employee Name"),
            DestinationField(name="Work Email"),
        ],
        sources=[SourceFile(key="source1", file_path=str(source_path))],
        mappings=[
            DraftMapping(
                destination_field="Employee Name",
                source_key="source1",
                source_column="Name",
            )
        ],
    )

    output_path = tmp_path / "output.xlsx"
    result = ReportGenerator().export(template, output_path)

    df = pd.read_excel(result)
    assert "Employee Name" in df.columns
    assert "Work Email" in df.columns
    assert len(df) == 1
    assert df["Employee Name"][0] == "Ada"
    assert pd.isna(df["Work Email"][0])
