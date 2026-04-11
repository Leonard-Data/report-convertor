"""Local template persistence for the MVP."""

from __future__ import annotations

from pathlib import Path
import json

from report_convertor.models.template import TemplateDraft


class LocalTemplateRepository:
    """Store template definitions as JSON files on disk."""

    def list_templates(self, templates_dir: Path) -> list[str]:
        """Return template names available in a directory.

        Args:
            templates_dir: Directory containing JSON template files.
        """

        directory = templates_dir.expanduser()
        if not directory.exists():
            return []
        return sorted(path.stem for path in directory.glob("*.json"))

    def load_template(
        self,
        identifier: str,
        templates_dir: Path,
    ) -> TemplateDraft:
        """Load a template by name or explicit file path.

        Args:
            identifier: Template name or JSON file path.
            templates_dir: Default directory used for name-based lookup.
        """

        path = self._resolve_path(identifier, templates_dir)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return TemplateDraft.model_validate(payload).ensure_mapping_rows()

    def save_template(
        self,
        template: TemplateDraft,
        templates_dir: Path,
    ) -> Path:
        """Save a template definition as formatted JSON.

        Args:
            template: Template model to persist.
            templates_dir: Output directory for the saved template file.
        """

        directory = templates_dir.expanduser()
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / f"{template.template_name}.json"
        destination.write_text(
            template.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return destination

    def _resolve_path(self, identifier: str, templates_dir: Path) -> Path:
        """Resolve a template identifier into a JSON file path.

        Args:
            identifier: Template name or explicit JSON file path.
            templates_dir: Default directory used for name-based lookup.
        """

        candidate = Path(identifier).expanduser()
        if candidate.suffix == ".json" and candidate.exists():
            return candidate

        target = templates_dir.expanduser() / f"{identifier}.json"
        if target.exists():
            return target
        raise FileNotFoundError(f"Template not found: {identifier}")
