"""Read Excel workbook metadata, headers, and frames."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from report_convertor.models.template import SourceFile


class WorkbookReader:
    """Read workbook headers and mapped columns with pandas."""

    def list_sheets(self, file_path: str | Path) -> list[str]:
        """Return sheet names from a workbook.

        Args:
            file_path: Workbook path to inspect.
        """

        workbook = pd.ExcelFile(Path(file_path).expanduser())
        return workbook.sheet_names

    def list_columns_from_path(
        self,
        file_path: str | Path,
        sheet_name: str | None = None,
    ) -> list[str]:
        """Return column names for a workbook path.

        Args:
            file_path: Workbook path to inspect.
            sheet_name: Optional sheet name. The first sheet is used when omitted.
        """

        frame = self.read_frame_from_path(file_path, sheet_name)
        return [str(column) for column in frame.columns]

    def list_columns(self, source: SourceFile) -> list[str]:
        """Return column names for a configured source workbook.

        Args:
            source: Source configuration containing workbook and sheet details.
        """

        return self.list_columns_from_path(source.file_path, source.sheet_name)

    def read_frame(self, source: SourceFile) -> pd.DataFrame:
        """Read a workbook sheet into a DataFrame.

        Args:
            source: Source configuration containing workbook and sheet details.
        """

        return self.read_frame_from_path(source.file_path, source.sheet_name)

    def read_frame_from_path(
        self,
        file_path: str | Path,
        sheet_name: str | None = None,
    ) -> pd.DataFrame:
        """Read a workbook path into a DataFrame.

        Args:
            file_path: Workbook path to read.
            sheet_name: Optional sheet name. The first sheet is used when omitted.
        """

        path = Path(file_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")
        return pd.read_excel(path, sheet_name=sheet_name or 0)
