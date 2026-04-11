"""Pure helpers used by the template editor widget."""

from __future__ import annotations

from report_convertor.features.sources.workbook_reader import WorkbookReader
from report_convertor.models.template import DraftMapping, SourceFile, TemplateDraft


def normalize_mappings(
    mappings: list[DraftMapping],
    destination_names: list[str],
    sources: list[SourceFile],
) -> list[DraftMapping]:
    """Keep only mappings that still match the current editor state."""

    source_keys = {source.key for source in sources}
    rows = []
    for mapping in mappings:
        if mapping.destination_field not in destination_names:
            continue
        if mapping.source_key and mapping.source_key not in source_keys:
            mapping = mapping.model_copy(update={"source_key": None, "source_column": None})
        rows.append(mapping)
    return rows


def refresh_source_columns(
    reader: WorkbookReader,
    sources: list[SourceFile],
) -> dict[str, list[str]]:
    """Collect source columns for every known source workbook."""

    columns: dict[str, list[str]] = {}
    for source in sources:
        try:
            columns[source.key] = reader.list_columns(source)
        except (FileNotFoundError, ValueError, OSError):
            columns[source.key] = []
    return columns


def merge_destination_names(existing: list[str], imported: list[str]) -> list[str]:
    """Append imported destination names without duplicates."""

    return existing + [name for name in imported if name not in existing]


def summary_text(display_name: str, draft: TemplateDraft) -> str:
    """Build the short status summary shown above the editor."""

    complete = sum(1 for mapping in draft.mappings if mapping.is_complete)
    return (
        f"Template: {display_name or '[draft]'} | "
        f"Destination Fields: {len(draft.destination_fields)} | "
        f"Sources: {len(draft.sources)} | "
        f"Mappings: {complete} complete"
    )
