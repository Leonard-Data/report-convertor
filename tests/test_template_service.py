"""Tests for template authoring services."""

from pathlib import Path

import pandas as pd

from report_convertor.features.templates.service import TemplateService


def test_service_imports_destination_headers(tmp_path: Path) -> None:
    """The service should read destination headers from a workbook."""

    workbook = tmp_path / "destination.xlsx"
    pd.DataFrame({"Employee Name": [], "Work Email": []}).to_excel(workbook, index=False)

    fields = TemplateService().import_destination_fields(str(workbook))

    assert [field.name for field in fields] == ["Employee Name", "Work Email"]


def test_service_creates_unique_source_keys(tmp_path: Path) -> None:
    """Source keys should remain unique when adding duplicate file names."""

    workbook = tmp_path / "source report.xlsx"
    workbook.write_text("placeholder", encoding="utf-8")

    service = TemplateService()
    first = service.create_source(str(workbook), {"source_report"})
    second = service.create_source(str(workbook), {first.key, "source_report"})

    assert first.key == "source_report_2"
    assert second.key == "source_report_3"
