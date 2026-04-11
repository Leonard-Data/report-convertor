"""Pydantic models for editable template drafts and final templates."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("value cannot be empty")
    return cleaned


def _optional(value: str | None) -> str | None:
    return value.strip() or None if value is not None else None


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class DestinationField(BaseModel):
    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return _required(value)


class SourceFile(BaseModel):
    key: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    sheet_name: str | None = None

    @field_validator("key", "file_path")
    @classmethod
    def clean_required(cls, value: str) -> str:
        return _required(value)

    @field_validator("sheet_name")
    @classmethod
    def clean_optional(cls, value: str | None) -> str | None:
        return _optional(value)

    @property
    def resolved_path(self) -> Path:
        return Path(self.file_path).expanduser()


class DraftMapping(BaseModel):
    destination_field: str = Field(min_length=1)
    source_key: str | None = None
    source_column: str | None = None

    @field_validator("destination_field")
    @classmethod
    def clean_destination(cls, value: str) -> str:
        return _required(value)

    @field_validator("source_key", "source_column")
    @classmethod
    def clean_optional(cls, value: str | None) -> str | None:
        return _optional(value)

    @property
    def is_complete(self) -> bool:
        return bool(self.source_key and self.source_column)


class FieldMapping(BaseModel):
    destination_field: str = Field(min_length=1)
    source_key: str = Field(min_length=1)
    source_column: str = Field(min_length=1)

    @field_validator("destination_field", "source_key", "source_column")
    @classmethod
    def clean_fields(cls, value: str) -> str:
        return _required(value)


class TemplateDraft(BaseModel):
    """Editable template state persisted as JSON and used by the GUI."""

    model_config = ConfigDict(extra="forbid")

    template_name: str = Field(min_length=1)
    output_file: str = Field(default="output.xlsx", min_length=1)
    destination_fields: list[DestinationField] = Field(default_factory=list)
    sources: list[SourceFile] = Field(default_factory=list)
    mappings: list[DraftMapping] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def add_legacy_destination_fields(cls, value: object) -> object:
        if not isinstance(value, dict) or value.get("destination_fields"):
            return value
        seen, fields = set(), []
        for mapping in value.get("mappings", []):
            name = str(mapping.get("destination_field", "")).strip()
            if name and name not in seen:
                seen.add(name)
                fields.append({"name": name})
        if fields:
            value["destination_fields"] = fields
        return value

    @field_validator("template_name", "output_file")
    @classmethod
    def clean_root(cls, value: str) -> str:
        return _required(value)

    @model_validator(mode="after")
    def validate_relationships(self) -> "TemplateDraft":
        destination_names = [field.name for field in self.destination_fields]
        source_keys = [source.key for source in self.sources]
        mapping_names = [mapping.destination_field for mapping in self.mappings]
        _unique(destination_names, "destination fields")
        _unique(source_keys, "source keys")
        _unique(mapping_names, "mapping destination fields")
        if set(mapping_names) - set(destination_names):
            raise ValueError("mappings reference unknown destination fields")
        missing_sources = {
            mapping.source_key
            for mapping in self.mappings
            if mapping.source_key and mapping.source_key not in source_keys
        }
        if missing_sources:
            raise ValueError(f"unknown mapping source keys: {', '.join(sorted(missing_sources))}")
        return self

    def ensure_mapping_rows(self) -> "TemplateDraft":
        """Return a draft with one editable mapping row per destination field."""

        existing = {mapping.destination_field: mapping for mapping in self.mappings}
        rows = [existing.get(field.name, DraftMapping(destination_field=field.name)) for field in self.destination_fields]
        return self.model_copy(update={"mappings": rows})

    def to_definition(self) -> "TemplateDefinition":
        """Convert a draft into a generation-ready template definition."""

        if not self.destination_fields:
            raise ValueError("at least one destination field is required")
        by_name = {mapping.destination_field: mapping for mapping in self.mappings}
        completed = []
        for field in self.destination_fields:
            mapping = by_name.get(field.name)
            if mapping is None or not mapping.is_complete:
                raise ValueError(f"Destination field '{field.name}' is not fully mapped")
            completed.append(FieldMapping.model_validate(mapping.model_dump()))
        return TemplateDefinition(
            template_name=self.template_name,
            output_file=self.output_file,
            sources=self.sources,
            mappings=completed,
        )


class TemplateDefinition(BaseModel):
    """Completed template definition used by preview and export services."""

    model_config = ConfigDict(extra="forbid")

    template_name: str = Field(min_length=1)
    output_file: str = Field(default="output.xlsx", min_length=1)
    sources: list[SourceFile]
    mappings: list[FieldMapping]

    @field_validator("template_name", "output_file")
    @classmethod
    def clean_root(cls, value: str) -> str:
        return _required(value)

    @model_validator(mode="after")
    def validate_relationships(self) -> "TemplateDefinition":
        source_keys = [source.key for source in self.sources]
        _unique(source_keys, "source keys")
        if not self.mappings:
            raise ValueError("at least one mapping is required")
        missing_sources = {mapping.source_key for mapping in self.mappings if mapping.source_key not in source_keys}
        if missing_sources:
            raise ValueError(f"unknown mapping source keys: {', '.join(sorted(missing_sources))}")
        return self

    @property
    def source_map(self) -> dict[str, SourceFile]:
        return {source.key: source for source in self.sources}
