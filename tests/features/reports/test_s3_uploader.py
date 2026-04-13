"""Tests for S3Uploader."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from report_convertor.features.reports.s3_uploader import S3Uploader


class TestUpload:
    """Tests for upload method."""

    def test_upload_success_returns_key_and_url(self, s3_config):
        """Upload returns key, url, version."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            with patch("pathlib.Path.exists", return_value=True):
                uploader = S3Uploader(s3_config)
                result = uploader.upload("test.xlsx", filename="report.xlsx")

        assert "key" in result
        assert "url" in result
        assert "version" in result
        assert result["url"] == f"s3://{s3_config.bucket}/{result['key']}"

    def test_upload_file_not_found_raises(self, s3_config):
        """Missing file raises FileNotFoundError."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            with patch("pathlib.Path.exists", return_value=False):
                uploader = S3Uploader(s3_config)
                with pytest.raises(FileNotFoundError, match="not found"):
                    uploader.upload("nonexistent.xlsx")

    def test_upload_with_version_appends_suffix(self, s3_config):
        """Version param creates filename_vX.ext."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.stem", "report"):
                    with patch("pathlib.Path.suffix", ".xlsx"):
                        uploader = S3Uploader(s3_config)
                        result = uploader.upload("report.xlsx", version="v1")

        assert "v1" in result["key"]

    def test_upload_with_custom_filename(self, s3_config):
        """Custom filename overrides source."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            with patch("pathlib.Path.exists", return_value=True):
                uploader = S3Uploader(s3_config)
                result = uploader.upload("original.xlsx", filename="custom.xlsx")

        assert "custom.xlsx" in result["key"]

    def test_upload_calls_correct_bucket(self, s3_config):
        """Uses configured bucket."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            with patch("pathlib.Path.exists", return_value=True):
                uploader = S3Uploader(s3_config)
                uploader.upload("test.xlsx")

        mock_client.upload_file.assert_called_once()
        call_args = mock_client.upload_file.call_args
        assert call_args[0][1] == s3_config.bucket


class TestUploadBytes:
    """Tests for upload_bytes method."""

    def test_upload_bytes_success(self, s3_config):
        """Raw bytes upload succeeds."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            uploader = S3Uploader(s3_config)
            result = uploader.upload_bytes(b"excel content", "report.xlsx")

        mock_client.put_object.assert_called_once()
        call_kwargs = mock_client.put_object.call_args.kwargs
        assert call_kwargs["Body"] == b"excel content"
        assert "report.xlsx" in call_kwargs["Key"]

    def test_upload_bytes_with_version(self, s3_config):
        """Version suffix applied."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            uploader = S3Uploader(s3_config)
            result = uploader.upload_bytes(b"data", "report.xlsx", version="v1")

        assert "v1" in result["key"]

    def test_upload_bytes_content_type_excel(self, s3_config):
        """Correct ContentType set."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            uploader = S3Uploader(s3_config)
            uploader.upload_bytes(b"content", "report.xlsx")

        call_kwargs = mock_client.put_object.call_args.kwargs
        assert (
            call_kwargs["ContentType"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


class TestListReports:
    """Tests for list_reports method."""

    def test_list_reports_filters_xlsx(self, s3_config):
        """Only Excel files returned."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {
                    "Key": "reports/report1.xlsx",
                    "Size": 100,
                    "LastModified": "2024-01-01",
                },
                {
                    "Key": "reports/report2.xls",
                    "Size": 200,
                    "LastModified": "2024-01-02",
                },
                {"Key": "reports/readme.txt", "Size": 50, "LastModified": "2024-01-03"},
            ]
        }

        with patch("boto3.client", return_value=mock_client):
            uploader = S3Uploader(s3_config)
            result = uploader.list_reports()

        assert len(result) == 2
        assert all(r["key"].endswith((".xlsx", ".xls")) for r in result)

    def test_list_reports_with_prefix(self, s3_config):
        """Prefix filter works."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {
                    "Key": "reports/monthly_report.xlsx",
                    "Size": 100,
                    "LastModified": "2024-01-01",
                },
                {
                    "Key": "reports/weekly_report.xlsx",
                    "Size": 150,
                    "LastModified": "2024-01-02",
                },
                {"Key": "reports/other.xlsx", "Size": 50, "LastModified": "2024-01-03"},
            ]
        }

        with patch("boto3.client", return_value=mock_client):
            uploader = S3Uploader(s3_config)
            result = uploader.list_reports(prefix="monthly")

        assert len(result) == 1
        assert "monthly" in result[0]["key"]

    def test_list_reports_includes_metadata(self, s3_config):
        """Returns size and last_modified."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {
                    "Key": "reports/report.xlsx",
                    "Size": 1024,
                    "LastModified": "2024-01-01",
                },
            ]
        }

        with patch("boto3.client", return_value=mock_client):
            uploader = S3Uploader(s3_config)
            result = uploader.list_reports()

        assert result[0]["size"] == 1024
        assert "last_modified" in result[0]


class TestGetClient:
    """Tests for get_client method."""

    def test_get_client_returns_s3_client(self, s3_config):
        """Returns the underlying S3 client."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            uploader = S3Uploader(s3_config)
            result = uploader.get_client()

        assert result == mock_client

    def test_config_returns_s3_config(self, s3_config):
        """Returns the S3 configuration."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            uploader = S3Uploader(s3_config)
            result = uploader.config

        assert result == s3_config
