"""UTC-first datetime utilities for consistent datetime handling.

All functions in this module assume and enforce UTC timezone to avoid
timezone-related bugs. All functions handle None gracefully for optional fields.
"""

from datetime import UTC, datetime
from typing import overload


def utc_now() -> datetime:
    """Get current UTC datetime (timezone-aware).

    Replaces deprecated datetime.utcnow() with timezone-aware alternative.

    Returns:
        Current datetime in UTC timezone.

    Example:
        >>> now = utc_now()
        >>> now.tzinfo == timezone.utc
        True
    """
    return datetime.now(UTC)


def ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure a datetime is in UTC timezone.

    If the datetime is naive, assumes it's already UTC.
    If it has a timezone, converts to UTC.

    Args:
        dt: Datetime to ensure is UTC, or None.

    Returns:
        UTC datetime or None if input was None.

    Example:
        >>> from datetime import datetime, timezone, timedelta
        >>> dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
        >>> utc_dt = ensure_utc(dt)
        >>> utc_dt.hour  # Converted from EST to UTC
        17
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return dt.replace(tzinfo=UTC)

    # Already timezone-aware, convert to UTC
    return dt.astimezone(UTC)


@overload
def parse_datetime(value: str) -> datetime:
    """Parse datetime from string."""
    ...


@overload
def parse_datetime(value: datetime) -> datetime:
    """Return datetime as-is."""
    ...


@overload
def parse_datetime(value: None) -> None:
    """Return None."""
    ...


def parse_datetime(value: str | datetime | None) -> datetime | None:
    """Parse ISO datetime string or return datetime/None as-is.

    Supports ISO format strings with or without 'Z' suffix.
    Handles both timezone-aware and naive datetime strings.

    Args:
        value: ISO datetime string, datetime object, or None.

    Returns:
        Parsed datetime in UTC, original datetime, or None.

    Raises:
        ValueError: If string cannot be parsed as datetime.

    Example:
        >>> parse_datetime("2024-01-01T12:00:00Z")
        datetime.datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        >>> parse_datetime("2024-01-01T12:00:00+00:00")
        datetime.datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        >>> parse_datetime(None)
        None
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return ensure_utc(value)

    if not isinstance(value, str):
        raise TypeError(f"Expected str, datetime, or None, got {type(value)}")

    # Try parsing ISO format with Z suffix
    if value.endswith("Z"):
        # Replace Z with +00:00 for Python compatibility
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            # Fallback: try without Z
            return datetime.fromisoformat(value[:-1]).replace(tzinfo=UTC)

    # Try parsing as ISO format
    try:
        dt = datetime.fromisoformat(value)
        # If naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError as e:
        raise ValueError(f"Could not parse datetime string: {value}") from e


def format_datetime(dt: datetime | None, fmt: str = "iso") -> str | None:
    """Format datetime to string.

    Args:
        dt: Datetime to format, or None.
        fmt: Format preset. Options:
            - "iso": ISO 8601 format with Z suffix (default)
            - "human": Human-readable format
            - "date": Date only (YYYY-MM-DD)

    Returns:
        Formatted string or None if input was None.

    Example:
        >>> dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        >>> format_datetime(dt)
        '2024-01-01T12:00:00Z'
        >>> format_datetime(dt, "date")
        '2024-01-01'
    """
    if dt is None:
        return None

    # Ensure UTC
    dt_utc = ensure_utc(dt)
    if dt_utc is None:
        return None

    if fmt == "iso":
        # ISO 8601 with Z suffix
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ").replace(".000000", "")
    elif fmt == "human":
        return dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    elif fmt == "date":
        return dt_utc.strftime("%Y-%m-%d")
    else:
        raise ValueError(f"Unknown format: {fmt}")
