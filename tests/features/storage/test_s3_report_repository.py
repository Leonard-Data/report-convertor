"""Tests for S3ReportRepository."""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from report_convertor.features.storage.s3_report_repository import S3ReportRepository


class TestListReportsWithFolders:
    """Tests for list_reports_with_folders method."""

    def test_list_reports_with_folders_returns_folder_structure(self, s3_config):
        """Returns correct folder/file structure from S3 keys."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "reports/Q1/report.xlsx"},
                {"Key": "reports/Q2/report.xlsx"},
                {"Key": "reports/report.xlsx"},
            ]
        }

        with patch("boto3.client", return_value=mock_client):
            repo = S3ReportRepository(s3_config)
            result = repo.list_reports_with_folders()

        assert len(result) == 3
        assert result[0] == {"folder": "", "file": "report.xlsx", "key": "report.xlsx"}
        assert result[1] == {
            "folder": "Q1",
            "file": "report.xlsx",
            "key": "Q1/report.xlsx",
        }
        assert result[2] == {
            "folder": "Q2",
            "file": "report.xlsx",
            "key": "Q2/report.xlsx",
        }

    def test_list_reports_with_folders_excludes_folder_markers(self, s3_config):
        """Keys ending with / are excluded as they are folder markers."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "reports/folder/"},
                {"Key": "reports/folder/file.xlsx"},
                {"Key": "reports/other/"},
            ]
        }

        with patch("boto3.client", return_value=mock_client):
            repo = S3ReportRepository(s3_config)
            result = repo.list_reports_with_folders()

        assert len(result) == 1
        assert result[0] == {
            "folder": "folder",
            "file": "file.xlsx",
            "key": "folder/file.xlsx",
        }

    def test_list_reports_with_folders_empty_bucket_returns_empty_list(self, s3_config):
        """No objects returns empty list."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {}

        with patch("boto3.client", return_value=mock_client):
            repo = S3ReportRepository(s3_config)
            result = repo.list_reports_with_folders()

        assert result == []

    def test_list_reports_with_folders_client_error_returns_empty_list(self, s3_config):
        """ClientError gracefully returns empty list."""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_client.list_objects_v2.side_effect = ClientError(
            {"Error": {"Code": "500"}}, "ListObjectsV2"
        )

        with patch("boto3.client", return_value=mock_client):
            repo = S3ReportRepository(s3_config)
            result = repo.list_reports_with_folders()

        assert result == []

    def test_list_reports_with_folders_sorts_by_folder_then_file(self, s3_config):
        """Results are sorted by folder then filename."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "reports/zebra/file.xlsx"},
                {"Key": "reports/alpha/report.xlsx"},
                {"Key": "reports/report.xlsx"},
            ]
        }

        with patch("boto3.client", return_value=mock_client):
            repo = S3ReportRepository(s3_config)
            result = repo.list_reports_with_folders()

        assert result[0]["file"] == "report.xlsx"
        assert result[1]["folder"] == "alpha"
        assert result[2]["folder"] == "zebra"

    def test_list_reports_with_folders_handles_pagination(self, s3_config):
        """Fetches all pages when IsTruncated is True."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.side_effect = [
            {
                "Contents": [
                    {"Key": "reports/folder1/file1.xlsx"},
                    {"Key": "reports/folder1/file2.xlsx"},
                ],
                "IsTruncated": True,
                "NextContinuationToken": "token_page2",
            },
            {
                "Contents": [
                    {"Key": "reports/folder2/file3.xlsx"},
                ],
                "IsTruncated": False,
            },
        ]

        with patch("boto3.client", return_value=mock_client):
            repo = S3ReportRepository(s3_config)
            result = repo.list_reports_with_folders()

        assert len(result) == 3
        assert mock_client.list_objects_v2.call_count == 2

    def test_list_reports_with_folders_files_in_root_folder(self, s3_config):
        """Files in root prefix have empty folder."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "reports/root.xlsx"},
                {"Key": "reports/nested/file.xlsx"},
            ]
        }

        with patch("boto3.client", return_value=mock_client):
            repo = S3ReportRepository(s3_config)
            result = repo.list_reports_with_folders()

        assert result[0] == {"folder": "", "file": "root.xlsx", "key": "root.xlsx"}
        assert result[1] == {
            "folder": "nested",
            "file": "file.xlsx",
            "key": "nested/file.xlsx",
        }


class TestListReports:
    """Tests for list_reports method."""

    def test_list_reports_empty_bucket_returns_empty_list(self, s3_config):
        """No objects returns empty list."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {}

        with patch("boto3.client", return_value=mock_client):
            repo = S3ReportRepository(s3_config)
            result = repo.list_reports()

        assert result == []

    def test_list_reports_client_error_returns_empty_list(self, s3_config):
        """ClientError gracefully returns empty list."""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_client.list_objects_v2.side_effect = ClientError(
            {"Error": {"Code": "500"}}, "ListObjectsV2"
        )

        with patch("boto3.client", return_value=mock_client):
            repo = S3ReportRepository(s3_config)
            result = repo.list_reports()

        assert result == []

    def test_list_reports_excludes_folders(self, s3_config):
        """Folders (keys ending with /) are excluded."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "reports/folder/"},
                {"Key": "reports/file.xlsx"},
            ]
        }

        with patch("boto3.client", return_value=mock_client):
            repo = S3ReportRepository(s3_config)
            result = repo.list_reports()

        assert result == ["file.xlsx"]


class TestDownloadReport:
    """Tests for download_report method."""

    def test_download_report_returns_cached_path_if_exists(self, s3_config, tmp_path):
        """If file exists in cache, returns cached path without downloading."""
        cache_dir = tmp_path / "reports"
        cache_dir.mkdir()

        test_file = cache_dir / "test.xlsx"
        test_file.write_bytes(b"cached content")

        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            with patch.object(S3ReportRepository, "CACHE_DIR", cache_dir):
                repo = S3ReportRepository(s3_config)
                result = repo.download_report("test.xlsx")

        assert result == test_file
        mock_client.get_object.assert_not_called()

    def test_download_report_downloads_and_caches(self, s3_config, tmp_path):
        """If file not in cache, downloads from S3 and saves to cache."""
        cache_dir = tmp_path / "reports"
        cache_dir.mkdir()

        mock_client = MagicMock()
        mock_client.get_object.return_value = {"Body": BytesIO(b"s3 content")}

        with patch("boto3.client", return_value=mock_client):
            with patch.object(S3ReportRepository, "CACHE_DIR", cache_dir):
                repo = S3ReportRepository(s3_config)
                result = repo.download_report("test.xlsx")

        assert result == cache_dir / "test.xlsx"
        assert result.read_bytes() == b"s3 content"
        mock_client.get_object.assert_called_once()

    def test_download_report_creates_parent_directories(self, s3_config, tmp_path):
        """Creates parent directories if they don't exist."""
        cache_dir = tmp_path / "reports" / "subfolder"
        assert not cache_dir.exists()

        mock_client = MagicMock()
        mock_client.get_object.return_value = {"Body": BytesIO(b"content")}

        with patch("boto3.client", return_value=mock_client):
            with patch.object(S3ReportRepository, "CACHE_DIR", cache_dir):
                repo = S3ReportRepository(s3_config)
                result = repo.download_report("file.xlsx")

        assert result.exists()
        assert result.parent == cache_dir

    def test_download_report_not_found_raises_file_not_found(self, s3_config, tmp_path):
        """Missing key raises FileNotFoundError."""
        from botocore.exceptions import ClientError

        cache_dir = tmp_path / "reports"
        cache_dir.mkdir()

        mock_client = MagicMock()
        mock_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "GetObject"
        )

        with patch("boto3.client", return_value=mock_client):
            with patch.object(S3ReportRepository, "CACHE_DIR", cache_dir):
                repo = S3ReportRepository(s3_config)
                with pytest.raises(FileNotFoundError, match="not found in S3"):
                    repo.download_report("nonexistent.xlsx")


class TestClearCache:
    """Tests for clear_cache method."""

    def test_clear_cache_removes_all_files(self, s3_config, tmp_path):
        """Removes all files from cache directory."""
        cache_dir = tmp_path / "reports"
        cache_dir.mkdir()

        (cache_dir / "file1.xlsx").write_bytes(b"content1")
        (cache_dir / "file2.xlsx").write_bytes(b"content2")
        (cache_dir / "file3.txt").write_bytes(b"text")

        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            with patch.object(S3ReportRepository, "CACHE_DIR", cache_dir):
                repo = S3ReportRepository(s3_config)
                deleted = repo.clear_cache()

        assert deleted == 3
        assert not list(cache_dir.iterdir())

    def test_clear_cache_empty_directory_returns_zero(self, s3_config, tmp_path):
        """Empty cache returns 0."""
        cache_dir = tmp_path / "reports"
        cache_dir.mkdir()

        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            with patch.object(S3ReportRepository, "CACHE_DIR", cache_dir):
                repo = S3ReportRepository(s3_config)
                deleted = repo.clear_cache()

        assert deleted == 0

    def test_clear_cache_nonexistent_directory_returns_zero(self, s3_config, tmp_path):
        """Non-existent cache directory returns 0."""
        cache_dir = tmp_path / "nonexistent"

        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            with patch.object(S3ReportRepository, "CACHE_DIR", cache_dir):
                repo = S3ReportRepository(s3_config)
                deleted = repo.clear_cache()

        assert deleted == 0


class TestCacheDirectoryCreation:
    """Tests for cache directory initialization."""

    def test_constructor_creates_cache_directory(self, s3_config, tmp_path):
        """Constructor creates cache directory if it doesn't exist."""
        cache_dir = tmp_path / "reports"

        with patch("boto3.client", return_value=MagicMock()):
            with patch.object(S3ReportRepository, "CACHE_DIR", cache_dir):
                repo = S3ReportRepository(s3_config)

        assert cache_dir.exists()
        assert cache_dir.is_dir()
