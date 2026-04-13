"""S3-based template persistence."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Protocol

import boto3
from botocore.exceptions import ClientError

from report_convertor.features.storage.config import S3Config
from report_convertor.models.template import TemplateDraft


class TemplateStorage(Protocol):
    """Protocol for template storage backends."""

    def list_templates(self) -> list[str]:
        """List template names available in storage."""
        ...

    def load_template(self, identifier: str) -> TemplateDraft:
        """Load a template by name."""
        ...

    def save_template(self, template: TemplateDraft) -> str:
        """Save a template, returns the storage key."""
        ...


class S3TemplateRepository:
    """Store template definitions as JSON files in S3."""

    def __init__(self, config: S3Config | None = None) -> None:
        """Create an S3 template repository.

        Args:
            config: Optional S3 configuration override.
        """
        self._config = config or S3Config.from_env()
        self._client = boto3.client(
            "s3",
            aws_access_key_id=self._config.access_key_id,
            aws_secret_access_key=self._config.secret_access_key,
            region_name=self._config.region,
        )

    def list_templates(self) -> list[str]:
        """Return unique template base names available in S3.

        Files are stored as ``{name}_{version}.json``. This method extracts the
        base name (everything before the last ``_``) so that versioned files are
        grouped under a single template entry.
        """
        try:
            response = self._client.list_objects_v2(
                Bucket=self._config.bucket,
                Prefix=self._config.folder,
            )
        except ClientError:
            return []

        names: set[str] = set()
        for obj in response.get("Contents", []):
            key = obj.get("Key", "")
            if key.endswith(".json"):
                filename = key[len(self._config.folder) : -5]  # strip folder + .json
                base = filename.rsplit("_", 1)[0] if "_" in filename else filename
                names.add(base)
        return sorted(names)

    def load_template(
        self, identifier: str, version: str | None = None
    ) -> TemplateDraft:
        """Load a template by name from S3, optionally by specific version."""
        if version:
            key = self._config.full_key(f"{identifier}_{version}.json")
        else:
            key = self._config.full_key(f"{identifier}.json")
        try:
            response = self._client.get_object(Bucket=self._config.bucket, Key=key)
            payload = response["Body"].read().decode("utf-8")
            data = json.loads(payload)
            return TemplateDraft.model_validate(data).ensure_mapping_rows()
        except ClientError as e:
            raise FileNotFoundError(f"Template not found in S3: {identifier}") from e

    def save_template(self, template: TemplateDraft, version: str | None = None) -> str:
        """Save a template to S3 with optional version.

        Args:
            template: Template to save.
            version: Optional version string (e.g., "v1", "v2"). If not provided,
                     uses timestamp.

        Returns:
            The S3 key where the template was saved.
        """
        base_name = template.template_name
        if version:
            file_key = f"{base_name}_{version}.json"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_key = f"{base_name}_{timestamp}.json"

        key = self._config.full_key(file_key)
        content = template.model_dump_json(indent=2)

        self._client.put_object(
            Bucket=self._config.bucket,
            Key=key,
            Body=content.encode("utf-8"),
            ContentType="application/json",
        )

        return key

    def list_versions(self, template_name: str) -> list[str]:
        """List available versions for a template.

        Returns version identifiers (e.g., ["v1", "v2", "0.0.0.1"]).
        Files follow the ``{template_name}_{version}.json`` convention; only
        the version suffix is returned.
        """
        prefix = self._config.full_key(f"{template_name}_")
        response = self._client.list_objects_v2(
            Bucket=self._config.bucket,
            Prefix=prefix,
        )

        template_prefix = f"{template_name}_"
        versions = []
        for obj in response.get("Contents", []):
            key = obj.get("Key", "")
            if key.endswith(".json"):
                filename = key[len(self._config.folder) :]  # strip folder prefix
                if filename.startswith(template_prefix):
                    version = filename[len(template_prefix) : -5]  # strip name_ + .json
                    if version:
                        versions.append(version)
        return sorted(versions)

    def get_client(self):
        """Return the underlying S3 client."""
        return self._client

    @property
    def config(self) -> S3Config:
        """Return the S3 configuration."""
        return self._config
