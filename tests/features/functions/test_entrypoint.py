"""Tests for CLI entrypoint functions."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from report_convertor.functions.entrypoint import (
    build_parser,
    main,
    _run_list,
    _run_generate,
)


class TestBuildParser:
    """Tests for build_parser function."""

    def test_build_parser_creates_parser(self):
        """Parser is created successfully."""
        parser = build_parser()
        assert parser is not None
        assert parser.prog == "report-convertor"

    def test_build_parser_list_command(self):
        """List command is added."""
        parser = build_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"

    def test_build_parser_generate_command(self):
        """Generate command requires template."""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["generate"])

    def test_build_parser_generate_with_template(self):
        """Generate with template parses correctly."""
        parser = build_parser()
        args = parser.parse_args(["generate", "-t", "TestTemplate"])
        assert args.command == "generate"
        assert args.template == "TestTemplate"

    def test_build_parser_generate_with_output(self):
        """Generate with output parses correctly."""
        parser = build_parser()
        args = parser.parse_args(
            ["generate", "-t", "TestTemplate", "-o", "output.xlsx"]
        )
        assert args.output == "output.xlsx"

    def test_build_parser_gui_command(self):
        """GUI command is added."""
        parser = build_parser()
        args = parser.parse_args(["gui"])
        assert args.command == "gui"

    def test_build_parser_preview_rows(self):
        """Preview rows option parses correctly."""
        parser = build_parser()
        args = parser.parse_args(
            ["generate", "-t", "TestTemplate", "--preview-rows", "5"]
        )
        assert args.preview_rows == 5


class TestMain:
    """Tests for main function."""

    def test_main_list_command(self):
        """List command returns 0."""
        with patch("report_convertor.functions.entrypoint._run_list") as mock_run:
            mock_run.return_value = 0
            result = main(["list"])
            assert result == 0
            mock_run.assert_called_once()

    def test_main_generate_command(self):
        """Generate command returns 0."""
        with patch("report_convertor.functions.entrypoint._run_generate") as mock_run:
            mock_run.return_value = 0
            result = main(["generate", "-t", "TestTemplate"])
            assert result == 0

    def test_main_gui_command(self):
        """GUI command returns 0."""
        with patch("report_convertor.functions.entrypoint._run_gui") as mock_run:
            mock_run.return_value = 0
            result = main(["gui"])
            assert result == 0

    def test_main_invalid_command_raises(self):
        """Invalid command raises SystemExit."""
        with patch("sys.argv", ["report-convertor", "invalid"]):
            with pytest.raises(SystemExit):
                main()


class TestRunList:
    """Tests for _run_list function."""

    def test_run_list_with_templates(self, tmp_path):
        """Returns list of templates."""
        (tmp_path / "template1.json").write_text(
            json.dumps({"template_name": "template1"})
        )
        (tmp_path / "template2.json").write_text(
            json.dumps({"template_name": "template2"})
        )

        result = _run_list(tmp_path)
        assert result == 0

    def test_run_list_empty_directory(self, tmp_path):
        """Returns 0 for empty directory."""
        result = _run_list(tmp_path)
        assert result == 0


class TestRunGenerate:
    """Tests for _run_generate function."""

    def test_run_generate_local_template(self, tmp_path):
        """Generates report from local template."""
        with patch(
            "report_convertor.features.templates.service.TemplateService.load_template"
        ) as mock_load:
            from report_convertor.models.template import TemplateDraft

            draft = TemplateDraft(
                template_name="TestTemplate",
                output_file="test_output.xlsx",
                sources=[],
                destination_fields=[],
            )
            mock_load.return_value = draft

            with patch(
                "report_convertor.features.templates.service.TemplateService.build_definition"
            ) as mock_build:
                mock_definition = MagicMock()
                mock_build.return_value = mock_definition

                with patch(
                    "report_convertor.features.reports.generator.ReportGenerator.export"
                ) as mock_export:
                    mock_export.return_value = Path("C:/bob/templates/test_output.xlsx")

                    result = _run_generate("TestTemplate", tmp_path, None, 0)

                    assert result == 0

    def test_run_generate_preview_rows(self, tmp_path):
        """Preview prints rows and returns 0."""
        with patch(
            "report_convertor.features.templates.service.TemplateService.load_template"
        ) as mock_load:
            from report_convertor.models.template import TemplateDraft

            draft = TemplateDraft(
                template_name="TestTemplate",
                output_file="test_output.xlsx",
                sources=[],
                destination_fields=[],
            )
            mock_load.return_value = draft

            with patch(
                "report_convertor.features.mapping.preview_service.PreviewService.preview_rows"
            ) as mock_preview:
                mock_preview.return_value = [
                    ["row1"],
                    ["row2"],
                    ["row3"],
                ]

                result = _run_generate("TestTemplate", tmp_path, None, 3)

                assert result == 0
