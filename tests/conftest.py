"""Shared fixtures for PyQt6 component tests."""

import pytest

from report_convertor.models.template import DestinationField, DraftMapping, SourceFile, TemplateDraft


@pytest.fixture
def sample_template() -> TemplateDraft:
    """A draft template with sample mappings for testing."""

    return TemplateDraft(
        template_name="test-template",
        output_file="output.xlsx",
        destination_fields=[
            DestinationField(name="Employee Name"),
            DestinationField(name="Work Email"),
        ],
        sources=[SourceFile(key="source1", file_path="input.xlsx")],
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


@pytest.fixture
def sample_template_single_mapping() -> TemplateDraft:
    """A draft template with a single mapping."""

    return TemplateDraft(
        template_name="single-mapping-template",
        output_file="output.xlsx",
        destination_fields=[DestinationField(name="ID")],
        sources=[SourceFile(key="source1", file_path="input.xlsx")],
        mappings=[
            DraftMapping(
                destination_field="ID",
                source_key="source1",
                source_column="Id",
            ),
        ],
    )


@pytest.fixture
def sample_rows() -> list[dict[str, object]]:
    """Sample preview rows for testing preview table."""

    return [
        {"Employee Name": "Alice", "Work Email": "alice@example.com"},
        {"Employee Name": "Bob", "Work Email": "bob@example.com"},
    ]


@pytest.fixture
def sample_rows_with_none() -> list[dict[str, object]]:
    """Sample rows with None values for edge case testing."""

    return [
        {"Employee Name": "Alice", "Work Email": None},
    ]


@pytest.fixture
def sample_combo_items() -> list[str]:
    """Sample items for searchable combo box."""

    return ["Option A", "Option B", "Option C", "Item One", "Item Two"]
