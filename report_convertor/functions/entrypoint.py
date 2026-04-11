"""CLI and GUI entrypoint wiring."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from report_convertor.features.mapping.preview_service import PreviewService
from report_convertor.features.reports.generator import ReportGenerator
from report_convertor.features.templates.service import TemplateService
from report_convertor.utils.logging import configure_logging
from report_convertor.utils.paths import default_templates_dir


def build_parser() -> argparse.ArgumentParser:
    """Create the shared command-line parser."""

    parser = argparse.ArgumentParser(prog="report-convertor")
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--debug", action="store_true", help="Enable debug logging.")
    shared.add_argument(
        "--templates-dir",
        default=str(default_templates_dir()),
        help="Directory containing local template JSON files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", parents=[shared], help="List local template names.")

    run_parser = subparsers.add_parser(
        "run",
        parents=[shared],
        help="Generate a report from a template.",
    )
    run_parser.add_argument("--template", required=True, help="Template name or JSON path.")
    run_parser.add_argument("--output", help="Optional output workbook path.")
    run_parser.add_argument(
        "--preview-rows",
        type=int,
        default=0,
        help="Print preview rows instead of generating a full report when greater than zero.",
    )

    subparsers.add_parser("gui", parents=[shared], help="Launch the desktop application.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the selected command.

    Args:
        argv: Optional argument list for tests.
    """

    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.debug)
    templates_dir = Path(args.templates_dir).expanduser()

    try:
        if args.command == "list":
            return _run_list(templates_dir)
        if args.command == "run":
            return _run_report(args.template, templates_dir, args.output, args.preview_rows)
        if args.command == "gui":
            return _run_gui(templates_dir)
    except (FileNotFoundError, ValueError, OSError, ImportError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1

    parser.error(f"Unsupported command: {args.command}")
    return 2


def _run_list(templates_dir: Path) -> int:
    """Print available templates.

    Args:
        templates_dir: Directory containing local template JSON files.
    """

    names = TemplateService().list_templates(templates_dir)
    if not names:
        print("No templates found.")
        return 0
    print("Available Templates:")
    for name in names:
        print(f"- {name}")
    return 0


def _run_report(
    identifier: str,
    templates_dir: Path,
    output: str | None,
    preview_rows: int,
) -> int:
    """Generate a report or print preview rows.

    Args:
        identifier: Template name or JSON path.
        templates_dir: Directory containing local template JSON files.
        output: Optional output workbook path.
        preview_rows: Number of preview rows to print instead of exporting.
    """

    service = TemplateService()
    template = service.load_template(identifier, templates_dir)
    if preview_rows > 0:
        rows = PreviewService().preview_rows(template, row_count=preview_rows)
        for row in rows:
            print(row)
        return 0

    destination = ReportGenerator().export(service.build_definition(template), output)
    print(f"Report generated: {destination}")
    return 0


def _run_gui(templates_dir: Path) -> int:
    """Launch the GUI application.

    Args:
        templates_dir: Default template directory for the GUI session.
    """

    from report_convertor.functions.gui_app import run_gui

    return run_gui(templates_dir)
