"""Reads and writes rows of data in Excel (.xlsx) files."""

from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet


class ExcelManager:
    """Works with one Excel file, where the first row of a sheet holds the column names."""

    def __init__(self, file_path: Path | str):
        self._file_path = Path(file_path)

    def read_rows(self, sheet_name: str | None = None) -> list[dict]:
        """Returns each row as a dictionary of column name to value. Skips blank rows.

        Uses the active sheet if no name is given, and ignores columns with no name.
        A formula gives the result Excel last saved, or None if Excel never calculated it.
        """
        workbook = load_workbook(self._file_path, read_only=True, data_only=True)
        try:
            sheet = workbook[sheet_name] if sheet_name else workbook.active
            rows = sheet.iter_rows(values_only=True)
            column_names = self._read_column_names(next(rows, ()))
            return [
                {name: value for name, value in zip(column_names, row) if name is not None}
                for row in rows
                if any(value is not None for value in row)
            ]
        finally:
            workbook.close()

    def write_rows(self, rows: list[dict], sheet_name: str = "Sheet1", overwrite: bool = False):
        """Creates the file with one sheet, using each dictionary's keys as column names.

        Raises FileExistsError if the file exists, unless overwrite is True.
        """
        if self._file_path.exists() and not overwrite:
            raise FileExistsError(f"{self._file_path} already exists")

        # dict.fromkeys collects each column once, in the order it first appears.
        column_names = list(dict.fromkeys(name for row in rows for name in row))
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = sheet_name
        self._append_row(sheet, column_names)
        for row in rows:
            self._append_row(sheet, [row.get(name) for name in column_names])
        workbook.save(self._file_path)

    @staticmethod
    def _read_column_names(first_row: tuple) -> list[str | None]:
        column_names = [None if value is None else str(value).strip() for value in first_row]
        named_columns = [name for name in column_names if name is not None]
        if len(named_columns) != len(set(named_columns)):
            raise ValueError("The sheet has two columns with the same name")
        return column_names

    @staticmethod
    def _append_row(sheet: Worksheet, values: list):
        sheet.append(values)
        # Text starting with = must stay text, or Excel would run it as a formula.
        for cell in sheet[sheet.max_row]:
            if cell.data_type == "f":
                cell.data_type = "s"
