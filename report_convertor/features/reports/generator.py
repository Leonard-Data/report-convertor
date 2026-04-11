"""Build consolidated report output from a template definition."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from report_convertor.features.sources.workbook_reader import WorkbookReader
from report_convertor.models.template import TemplateDefinition, TemplateDraft


class ReportGenerator:
    """Generate preview data and exported reports from templates."""

    def __init__(self, reader: WorkbookReader | None = None) -> None:
        """Create a generator instance.

        Args:
            reader: Optional workbook reader override for tests.
        """

        self._reader = reader or WorkbookReader()

    def build_dataframe(self, template: TemplateDefinition | TemplateDraft) -> pd.DataFrame:
        """Build the output DataFrame defined by a template.

        Args:
            template: Template definition describing sources and mappings.
        """

        definition = template.to_definition() if isinstance(template, TemplateDraft) else template
        cache = {
            source.key: self._reader.read_frame(source)
            for source in definition.sources
        }
        output = {}
        for mapping in definition.mappings:
            output[mapping.destination_field] = self._mapped_series(cache, definition, mapping)
        return pd.DataFrame(output)

    def build_review_dataframe(self, template: TemplateDefinition | TemplateDraft) -> pd.DataFrame:
        """Build review rows using only completed mappings from a draft.

        Args:
            template: Template draft or final definition to preview.
        """

        if isinstance(template, TemplateDefinition):
            return self.build_dataframe(template)
        mappings = [mapping for mapping in template.mappings if mapping.is_complete]
        if not mappings:
            raise ValueError("At least one field must be mapped to generate a review.")
        cache = {source.key: self._reader.read_frame(source) for source in template.sources}
        source_map = {source.key: source for source in template.sources}
        output = {}
        for mapping in mappings:
            output[mapping.destination_field] = self._mapped_series(cache, type("DraftView", (), {"source_map": source_map})(), mapping)
        return pd.DataFrame(output)

    def export(
        self,
        template: TemplateDefinition | TemplateDraft,
        output_path: str | Path | None = None,
    ) -> Path:
        """Export a generated report to an Excel file.

        Args:
            template: Template definition describing the report.
            output_path: Optional destination override for the exported workbook.
        """

        definition = template.to_definition() if isinstance(template, TemplateDraft) else template
        destination = Path(output_path or definition.output_file).expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        frame = self.build_dataframe(definition)
        frame.to_excel(destination, index=False)
        return destination

    def _mapped_series(self, cache: dict[str, pd.DataFrame], template, mapping) -> pd.Series:
        source_frame = cache[mapping.source_key]
        if mapping.source_column not in source_frame.columns:
            message = (
                f"Column '{mapping.source_column}' not found in "
                f"{template.source_map[mapping.source_key].file_path}"
            )
            raise ValueError(message)
        return source_frame[mapping.source_column]
