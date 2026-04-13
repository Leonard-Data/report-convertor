"""Tests for S3TemplateRepository."""

import json
from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from report_convertor.features.templates.s3_repository import S3TemplateRepository
from report_convertor.models.template import (
    DestinationField,
    DraftMapping,
    SourceFile,
    TemplateDraft,
)


class TestListTemplates:
    """Tests for list_templates method."""

    def test_list_templates_returns_sorted_names(self, s3_config):
        """Valid S3 response returns sorted JSON filenames."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "templates/template2_v1.json"},
                {"Key": "templates/template1_v1.json"},
                {"Key": "templates/readme.txt"},
            ]
        }

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            result = repo.list_templates()

        assert result == ["template1", "template2"]

    def test_list_templates_extracts_base_name_from_versioned_files(self, s3_config):
        """Versioned files like name_0.0.0.1.json return only the base name."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "templates/TestGenerate_0.0.0.1.json"},
                {"Key": "templates/TestGenerate_0.0.0.2.json"},
                {"Key": "templates/SampleTemplate_v2.json"},
            ]
        }

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            result = repo.list_templates()

        assert result == ["SampleTemplate", "TestGenerate"]

    def test_list_templates_empty_bucket_returns_empty_list(self, s3_config):
        """No objects returns empty list."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {}

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            result = repo.list_templates()

        assert result == []

    def test_list_templates_client_error_returns_empty_list(self, s3_config):
        """ClientError gracefully returns empty list."""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_client.list_objects_v2.side_effect = ClientError(
            {"Error": {"Code": "500"}}, "ListObjectsV2"
        )

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            result = repo.list_templates()

        assert result == []


class TestLoadTemplate:
    """Tests for load_template method."""

    def test_load_template_success(self, s3_config, sample_template):
        """Valid template returns TemplateDraft."""
        mock_client = MagicMock()
        json_bytes = sample_template.model_dump_json().encode("utf-8")
        mock_client.get_object.return_value = {"Body": BytesIO(json_bytes)}

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            result = repo.load_template("test-template")

        assert result.template_name == sample_template.template_name

    def test_load_template_not_found_raises_file_not_found(self, s3_config):
        """Missing key raises FileNotFoundError."""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "GetObject"
        )

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            with pytest.raises(FileNotFoundError, match="not found in S3"):
                repo.load_template("nonexistent")

    def test_load_template_invalid_json_raises(self, s3_config):
        """Malformed JSON raises error."""
        mock_client = MagicMock()
        invalid_bytes = b"invalid json{"
        mock_client.get_object.return_value = {"Body": BytesIO(invalid_bytes)}

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            with pytest.raises(json.JSONDecodeError):
                repo.load_template("test-template")


class TestSaveTemplate:
    """Tests for save_template method."""

    def test_save_template_with_version(self, s3_config, sample_template):
        """Saves with version suffix."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            key = repo.save_template(sample_template, version="v1")

        mock_client.put_object.assert_called_once()
        call_kwargs = mock_client.put_object.call_args.kwargs
        assert "v1" in call_kwargs["Key"]
        assert key == "templates/test-template_v1.json"

    def test_save_template_without_version(self, s3_config, sample_template):
        """Saves with timestamp."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            key = repo.save_template(sample_template)

        mock_client.put_object.assert_called_once()
        call_kwargs = mock_client.put_object.call_args.kwargs
        assert "test-template_" in call_kwargs["Key"]
        assert ".json" in call_kwargs["Key"]

    def test_save_template_returns_key(self, s3_config, sample_template):
        """Returns correct S3 key."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            key = repo.save_template(sample_template, version="v2")

        assert key == "templates/test-template_v2.json"


class TestListVersions:
    """Tests for list_versions method."""

    def test_list_versions_returns_sorted(self, s3_config):
        """Returns sorted version list with only the version suffix."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "templates/test-template_v2.json"},
                {"Key": "templates/test-template_v1.json"},
                {"Key": "templates/test-template_20240415_143022.json"},
            ]
        }

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            result = repo.list_versions("test-template")

        assert result == sorted(result)
        assert len(result) == 3
        assert "v1" in result
        assert "v2" in result
        assert "20240415_143022" in result
        # Must not contain the template name prefix
        assert all("test-template" not in v for v in result)

    def test_list_versions_dotted_version(self, s3_config):
        """Dotted version like 0.0.0.1 is extracted correctly."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "templates/TestGenerate_0.0.0.1.json"},
                {"Key": "templates/TestGenerate_0.0.0.2.json"},
            ]
        }

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            result = repo.list_versions("TestGenerate")

        assert result == ["0.0.0.1", "0.0.0.2"]

    def test_list_versions_empty_returns_empty(self, s3_config):
        """No versions returns empty list."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {}

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            result = repo.list_versions("test-template")

        assert result == []


class TestGetClient:
    """Tests for get_client method."""

    def test_get_client_returns_s3_client(self, s3_config):
        """Returns the underlying S3 client."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            result = repo.get_client()

        assert result == mock_client

    def test_config_returns_s3_config(self, s3_config):
        """Returns the S3 configuration."""
        mock_client = MagicMock()

        with patch("boto3.client", return_value=mock_client):
            repo = S3TemplateRepository(s3_config)
            result = repo.config

        assert result == s3_config
