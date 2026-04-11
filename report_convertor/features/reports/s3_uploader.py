"""S3 upload service for generated reports."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from report_convertor.features.storage.config import S3Config


class S3Uploader:
    """Upload generated Excel reports to S3."""

    def __init__(self, config: S3Config | None = None) -> None:
        """Create an S3 uploader.

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

    def upload(
        self,
        local_path: Path | str,
        filename: str | None = None,
        version: str | None = None,
    ) -> dict:
        """Upload a file to S3.

        Args:
            local_path: Local file to upload.
            filename: Optional destination filename. Uses local filename if not provided.
            version: Optional version suffix (e.g., "v1", "20240415"). If provided,
                     prepends to extension: report_v1.xlsx.

        Returns:
            dict with 'key', 'url', and 'version' info.
        """
        source = Path(local_path)
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")

        base = filename or source.stem
        ext = source.suffix
        if version:
            dest_name = f"{base}_{version}{ext}"
        else:
            dest_name = f"{base}{ext}"

        key = self._config.full_key(dest_name)

        self._client.upload_file(
            str(source),
            self._config.bucket,
            key,
            ExtraArgs={
                "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            },
        )

        return {
            "key": key,
            "url": f"s3://{self._config.bucket}/{key}",
            "version": version or datetime.now().strftime("%Y%m%d_%H%M%S"),
            "local_path": str(source),
        }

    def upload_bytes(
        self,
        content: bytes,
        filename: str,
        version: str | None = None,
    ) -> dict:
        """Upload raw bytes to S3.

        Args:
            content: Raw file content.
            filename: Destination filename.
            version: Optional version suffix.

        Returns:
            dict with 'key', 'url', and 'version' info.
        """
        path = Path(filename)
        ext = path.suffix
        name = path.stem

        if version:
            dest_name = f"{name}_{version}{ext}"
        else:
            dest_name = filename

        key = self._config.full_key(dest_name)

        self._client.put_object(
            Bucket=self._config.bucket,
            Key=key,
            Body=content,
            ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        return {
            "key": key,
            "url": f"s3://{self._config.bucket}/{key}",
            "version": version,
        }

    def list_reports(self, prefix: str | None = None) -> list[dict]:
        """List reports in the S3 folder.

        Args:
            Optional prefix to filter filenames.

        Returns:
            List of dicts with 'key', 'size', 'last_modified'.
        """
        search_prefix = prefix or ""
        response = self._client.list_objects_v2(
            Bucket=self._config.bucket,
            Prefix=self._config.folder,
        )

        reports = []
        folder_len = len(self._config.folder)
        for obj in response.get("Contents", []):
            key = obj.get("Key", "")[folder_len:]
            if key.endswith((".xlsx", ".xls")):
                if prefix and not key.startswith(prefix):
                    continue
                reports.append(
                    {
                        "key": key,
                        "size": obj.get("Size", 0),
                        "last_modified": obj.get("LastModified"),
                    }
                )
        return reports

    def get_client(self):
        """Return the underlying S3 client."""
        return self._client

    @property
    def config(self) -> S3Config:
        """Return the S3 configuration."""
        return self._config
