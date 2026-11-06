"""Everything about the report: which rows it contains, and remembering what was sent.

Each report only contains rows dated after the newest row in the last report sent.
That date is saved in last_report_sent.json, once the report has actually been sent.
"""

import threading
from datetime import date, datetime, timezone
from pathlib import Path

from managers.mysql_manager import MySqlManager
from shared.json_serialization import from_json, to_json

# region CONFIGURATION
# The database table the report reads from.
REPORT_TABLE = "daily_report"
REPORT_COLUMNS = "*"  # Or a list of columns, such as "`Start`, `End`".
# Must be a DATE, DATETIME or TIMESTAMP column, written exactly as it is in the table.
REPORT_DATE_COLUMN = "End"

# The keys in the JSON sent to the client.
RESPONSE_REPORT_KEY = "report"
REPORT_DATE_AFTER_KEY = "samples_after"
REPORT_ROW_COUNT_KEY = "sample_count"
REPORT_ROWS_KEY = "samples"

# The file that remembers the last report sent, and its keys.
# After changing LAST_REPORT_DATE_KEY, update the key in the existing file, or it counts as damaged.
LAST_REPORT_SENT_FILE = Path(__file__).resolve().parents[2] / "last_report_sent.json"
LAST_REPORT_SENT_AT_KEY = "last_sent_at"
LAST_REPORT_DATE_KEY = "last_sample_date"
LAST_REPORT_ROW_COUNT_KEY = "sample_count"
# endregion

# Rows with no date can't be compared, so both queries leave them out.
SELECT_ALL_REPORT_ROWS_QUERY = (
    f"SELECT {REPORT_COLUMNS} FROM `{REPORT_TABLE}` "
    f"WHERE `{REPORT_DATE_COLUMN}` IS NOT NULL ORDER BY `{REPORT_DATE_COLUMN}` ASC"
)
SELECT_NEW_REPORT_ROWS_QUERY = (
    f"SELECT {REPORT_COLUMNS} FROM `{REPORT_TABLE}` "
    f"WHERE `{REPORT_DATE_COLUMN}` > %s ORDER BY `{REPORT_DATE_COLUMN}` ASC"
)

# Each client has its own thread, so only one at a time may use the file.
_last_report_file_lock = threading.Lock()


class LastReportFileError(Exception):
    """last_report_sent.json can't be used. The message explains what to do."""


# region CREATING THE REPORT
def create_report() -> dict:
    """Returns a report of the rows that haven't been sent yet."""
    sent_up_to = _get_last_date_sent()
    rows = _fetch_rows_after(sent_up_to)
    return {
        REPORT_DATE_AFTER_KEY: sent_up_to,
        REPORT_ROW_COUNT_KEY: len(rows),
        REPORT_ROWS_KEY: rows,
    }


def _fetch_rows_after(sent_up_to: datetime | None) -> list[dict]:
    with MySqlManager.from_environment() as database:
        if sent_up_to is None:
            return database.fetch_all(SELECT_ALL_REPORT_ROWS_QUERY)
        return database.fetch_all(SELECT_NEW_REPORT_ROWS_QUERY, (sent_up_to,))


# endregion


# region REMEMBERING WHAT WAS SENT
def mark_report_sent(report: dict):
    """Saves that this report was sent. A report with no rows changes nothing."""
    rows = report[REPORT_ROWS_KEY]
    if not rows:
        return

    newest_date = max(_to_datetime(row[REPORT_DATE_COLUMN]) for row in rows)
    with _last_report_file_lock:
        previous = _read_last_report_file()
        # Never move backwards, in case two clients' reports finish out of order.
        if previous is not None:
            newest_date = max(newest_date, previous[LAST_REPORT_DATE_KEY])
        _write_last_report_file(
            {
                LAST_REPORT_SENT_AT_KEY: datetime.now(timezone.utc),
                LAST_REPORT_DATE_KEY: newest_date,
                LAST_REPORT_ROW_COUNT_KEY: len(rows),
            }
        )


def _to_datetime(value) -> datetime:
    """Converts a DATE or DATETIME value, so either column type can be compared the same way."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    raise TypeError(f"{REPORT_DATE_COLUMN} must be a date column, but contains {value!r}")


def _get_last_date_sent() -> datetime | None:
    with _last_report_file_lock:
        last_report = _read_last_report_file()
    return None if last_report is None else last_report[LAST_REPORT_DATE_KEY]


def _read_last_report_file() -> dict | None:
    """Returns the file's contents, or None if no report has been sent yet."""
    if not LAST_REPORT_SENT_FILE.exists():
        return None
    try:
        last_report = from_json(LAST_REPORT_SENT_FILE.read_text(encoding="utf-8"))
        return {
            **last_report,
            LAST_REPORT_DATE_KEY: datetime.fromisoformat(last_report[LAST_REPORT_DATE_KEY]),
        }
    except (ValueError, KeyError, TypeError) as error:
        # Don't guess: treating this as "nothing sent yet" would resend every row.
        raise LastReportFileError(
            f"{LAST_REPORT_SENT_FILE} is damaged. Fix it, or delete it to send all rows again."
        ) from error


def _write_last_report_file(last_report: dict):
    # Writing a temporary file first means a crash can't leave a half-written file.
    temporary_file = LAST_REPORT_SENT_FILE.with_suffix(".json.tmp")
    temporary_file.write_text(to_json(last_report, indent=2) + "\n", encoding="utf-8")
    temporary_file.replace(LAST_REPORT_SENT_FILE)


# endregion
