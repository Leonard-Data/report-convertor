"""High-level template operations shared by CLI and GUI."""

from __future__ import annotations

from pathlib import Path

from report_convertor.features.sources.workbook_reader import WorkbookReader
from report_convertor.features.templates.repository import LocalTemplateRepository
from report_convertor.models.template import DestinationField, SourceFile, TemplateDefinition, TemplateDraft


class TemplateService:
    """Expose template operations without leaking repository details."""

    def __init__(
        self,
        repository: LocalTemplateRepository | None = None,
        reader: WorkbookReader | None = None,
    ) -> None:
        """Create a service instance.

        Args:
            repository: Optional repository override for tests or future adapters.
            reader: Optional workbook reader override for tests.
        """

        self._repository = repository or LocalTemplateRepository()
        self._reader = reader or WorkbookReader()

    def list_templates(self, templates_dir: Path) -> list[str]:
        """List template names from the active repository.

        Args:
            templates_dir: Directory containing template JSON files.
        """

        return self._repository.list_templates(templates_dir)

    def load_template(self, identifier: str, templates_dir: Path) -> TemplateDraft:
        """Load a template definition.

        Args:
            identifier: Template name or file path.
            templates_dir: Directory containing template JSON files.
        """

        return self._repository.load_template(identifier, templates_dir)

    def save_template(self, template: TemplateDraft, templates_dir: Path) -> Path:
        """Save a template definition.

        Args:
            template: Template model to persist.
            templates_dir: Directory containing template JSON files.
        """

        return self._repository.save_template(template, templates_dir)

    def build_definition(self, template: TemplateDraft) -> TemplateDefinition:
        """Convert a draft template into a generation-ready definition.

        Args:
            template: Draft template authored by the user.
        """

        return template.ensure_mapping_rows().to_definition()

    def import_destination_fields(
        self,
        file_path: str,
        sheet_name: str | None = None,
    ) -> list[DestinationField]:
        """Read destination fields from a workbook header row.

        Args:
            file_path: Workbook path used as the destination template.
            sheet_name: Optional sheet name. The first sheet is used when omitted.
        """

        return [
            DestinationField(name=column)
            for column in self._reader.list_columns_from_path(file_path, sheet_name)
        ]

    def create_source(
        self,
        file_path: str,
        existing_keys: set[str] | None = None,
        sheet_name: str | None = None,
    ) -> SourceFile:
        """Create a unique source entry for a workbook path.

        Args:
            file_path: Workbook path to add as a source.
            existing_keys: Existing source keys that must remain unique.
            sheet_name: Optional sheet name. The first sheet is used when omitted.
        """

        path = Path(file_path).expanduser()
        base = path.stem.replace(" ", "_") or "source"
        key = base
        used = existing_keys or set()
        suffix = 2
        while key in used:
            key = f"{base}_{suffix}"
            suffix += 1
        return SourceFile(key=key, file_path=str(path), sheet_name=sheet_name)
