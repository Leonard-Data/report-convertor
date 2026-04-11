"""Tests for draft and final template models."""

import pytest
from pydantic import ValidationError

from report_convertor.models.template import DestinationField, DraftMapping, SourceFile, TemplateDefinition, TemplateDraft


def test_template_rejects_unknown_mapping_source() -> None:
    """Completed templates must reference configured source keys."""

    payload = {
        "template_name": "demo",
        "output_file": "output.xlsx",
        "sources": [{"key": "source1", "file_path": "input.xlsx"}],
        "mappings": [{"destination_field": "Employee Name", "source_key": "missing", "source_column": "Name"}],
    }

    with pytest.raises(ValidationError):
        TemplateDefinition.model_validate(payload)


def test_draft_can_be_saved_with_incomplete_mapping() -> None:
    """Draft templates may contain destination fields before mapping is complete."""

    draft = TemplateDraft(
        template_name="draft-template",
        destination_fields=[DestinationField(name="Employee Name")],
        sources=[SourceFile(key="source1", file_path="input.xlsx")],
        mappings=[DraftMapping(destination_field="Employee Name")],
    )

    assert draft.mappings[0].is_complete is False


def test_draft_requires_complete_mappings_for_generation() -> None:
    """Draft templates must become complete before generation is allowed."""

    draft = TemplateDraft(
        template_name="draft-template",
        destination_fields=[DestinationField(name="Employee Name")],
        sources=[SourceFile(key="source1", file_path="input.xlsx")],
        mappings=[DraftMapping(destination_field="Employee Name")],
    )

    with pytest.raises(ValueError, match="not fully mapped"):
        draft.to_definition()
