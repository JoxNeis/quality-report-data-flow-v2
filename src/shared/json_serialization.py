"""Converts data to and from JSON, including the value types that MySQL and Excel return."""

import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal


def to_json(data, indent: int | None = None) -> str:
    """Returns data as JSON text. Raises TypeError or ValueError if it can't be converted."""
    # NaN and Infinity are rejected because they aren't valid JSON.
    return json.dumps(
        data, default=_convert_value, ensure_ascii=False, allow_nan=False, indent=indent
    )


def from_json(text: str):
    """Returns the data in JSON text. Raises ValueError if the text isn't valid JSON."""
    return json.loads(text)


def _convert_value(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    # Decimal becomes text, because a JSON number could lose precision.
    if isinstance(value, (Decimal, timedelta)):
        return str(value)
    raise TypeError(f"A value of type {type(value).__name__} can't be converted to JSON")
