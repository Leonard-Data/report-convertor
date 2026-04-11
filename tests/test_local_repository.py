"""Tests for the local JSON template repository."""

from pathlib import Path

from report_convertor.features.templates.repository import LocalTemplateRepository
from report_convertor.models.template import DestinationField, DraftMapping, SourceFile, TemplateDraft


def test_repository_saves_loads_and_lists_templates(tmp_path: Path) -> None:
    """The local repository should round-trip template files."""

    repository = LocalTemplateRepository()
    template = TemplateDraft(
        template_name="demo-template",
        output_file="output.xlsx",
        destination_fields=[DestinationField(name="Employee Name")],
        sources=[SourceFile(key="source1", file_path="input.xlsx")],
        mappings=[DraftMapping(destination_field="Employee Name")],
    )

    repository.save_template(template, tmp_path)

    names = repository.list_templates(tmp_path)
    loaded = repository.load_template("demo-template", tmp_path)

    assert names == ["demo-template"]
    assert loaded.template_name == template.template_name
    assert loaded.mappings[0].destination_field == "Employee Name"
    assert loaded.destination_fields[0].name == "Employee Name"
