"""Generate a preview of mapped report output."""

from __future__ import annotations

from report_convertor.features.reports.generator import ReportGenerator
from report_convertor.models.template import TemplateDefinition, TemplateDraft


class PreviewService:
    """Create preview rows from a template without exporting a file."""

    def __init__(self, generator: ReportGenerator | None = None) -> None:
        """Create a preview service.

        Args:
            generator: Optional report generator override for tests.
        """

        self._generator = generator or ReportGenerator()

    def preview_rows(
        self,
        template: TemplateDefinition | TemplateDraft,
        row_count: int = 10,
    ) -> list[dict[str, object]]:
        """Return the first mapped rows as dictionaries.

        Args:
            template: Template definition to evaluate.
            row_count: Number of preview rows to include.
        """

        frame = self._generator.build_review_dataframe(template)
        return frame.head(row_count).fillna("").to_dict(orient="records")
