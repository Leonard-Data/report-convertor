"""S3 report repository for listing and caching reports."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import boto3
from botocore.exceptions import ClientError

from report_convertor.features.storage.config import S3Config


class ReportStorage(Protocol):
    """Protocol for report storage backends."""

    def list_reports(self) -> list[str]:
        """List available reports."""
        ...

    def download_report(self, filename: str) -> Path:
        """Download a report to local cache."""
        ...


class S3ReportRepository:
    """List and download reports from S3 with local caching."""

    CACHE_DIR = Path("C:/bob/templates")

    def __init__(self, config: S3Config | None = None) -> None:
        """Create an S3 report repository.

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
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def list_reports(self) -> list[str]:
        """Return report filenames available in S3."""
        return [
            item["key"] for item in self.list_reports_with_folders() if item.get("file")
        ]

    def list_reports_with_folders(self) -> list[dict]:
        """Return report files with folder hierarchy.

        Returns:
            List of dicts with 'folder', 'file', and 'key' for each report.
        """
        try:
            response = self._client.list_objects_v2(
                Bucket=self._config.bucket,
                Prefix=self._config.report_folder,
            )
        except ClientError:
            return []

        result = []
        prefix_len = len(self._config.report_folder)
        for obj in response.get("Contents", []):
            key = obj.get("Key", "")
            if not key or key.endswith("/"):
                continue
            relative = key[prefix_len:]
            if "/" in relative:
                folder, filename = relative.split("/", 1)
                result.append({"folder": folder, "file": filename, "key": relative})
            else:
                result.append({"folder": "", "file": relative, "key": relative})
        return sorted(result, key=lambda x: (x["folder"], x["file"]))

    def download_report(self, filename: str) -> Path:
        """Download a report to local cache.

        If file already exists in cache, return cached path without re-downloading.

        Args:
            filename: Name of the file to download (relative key or just filename).

        Returns:
            Local path to the cached file.
        """
        local_path = self.CACHE_DIR / filename

        if local_path.exists():
            return local_path

        key = self._config.report_folder + filename
        if not key.startswith(self._config.report_folder):
            key = self._config.report_folder + filename
        try:
            response = self._client.get_object(
                Bucket=self._config.bucket,
                Key=key,
            )
            content = response["Body"].read()

            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(content)

            return local_path
        except ClientError as e:
            raise FileNotFoundError(f"Report not found in S3: {filename}") from e

    def download_report_by_key(self, key: str) -> Path:
        """Download a report by exact S3 key to local cache.

        If file already exists in cache, return cached path without re-downloading.

        Args:
            key: Exact S3 key of the file to download.

        Returns:
            Local path to the cached file.
        """
        safe_name = key.replace("/", "_")
        local_path = self.CACHE_DIR / safe_name

        if local_path.exists():
            return local_path

        try:
            response = self._client.get_object(
                Bucket=self._config.bucket,
                Key=key,
            )
            content = response["Body"].read()

            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(content)

            return local_path
        except ClientError as e:
            raise FileNotFoundError(f"Report not found in S3: {key}") from e

    def clear_cache(self, older_than_days: int | None = None) -> int:
        """Clear cached reports.

        Args:
            older_than_days: If provided, only delete files older than this many days.

        Returns:
            Number of files deleted.
        """
        import time

        if not self.CACHE_DIR.exists():
            return 0

        deleted = 0
        now = time.time()
        cutoff = older_than_days * 86400 if older_than_days else 0

        for file in self.CACHE_DIR.iterdir():
            if file.is_file():
                if older_than_days:
                    age = now - file.stat().st_mtime
                    if age < cutoff:
                        continue
                file.unlink()
                deleted += 1

        return deleted
