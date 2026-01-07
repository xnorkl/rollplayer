"""Tests for datetime utilities."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from gm_chatbot.lib.datetime import ensure_utc, format_datetime, parse_datetime, utc_now


class TestUtcNow:
    """Tests for utc_now function."""

    def test_returns_timezone_aware(self):
        """utc_now should return timezone-aware datetime."""
        result = utc_now()
        assert result.tzinfo == UTC

    def test_returns_current_time(self):
        """utc_now should return current time (approximately)."""
        before = datetime.now(UTC)
        result = utc_now()
        after = datetime.now(UTC)

        assert before <= result <= after


class TestEnsureUtc:
    """Tests for ensure_utc function."""

    def test_none_returns_none(self):
        """ensure_utc should return None for None input."""
        assert ensure_utc(None) is None

    def test_naive_datetime_assumes_utc(self):
        """Naive datetime should be assumed UTC."""
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        result = ensure_utc(naive_dt)

        assert result is not None
        assert result.tzinfo == UTC
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 12

    def test_utc_datetime_unchanged(self):
        """UTC datetime should remain unchanged."""
        utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = ensure_utc(utc_dt)

        assert result == utc_dt
        assert result.tzinfo == UTC

    def test_other_timezone_converts_to_utc(self):
        """Datetime in other timezone should convert to UTC."""
        est = timezone(timedelta(hours=-5))
        est_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=est)
        result = ensure_utc(est_dt)

        assert result is not None
        assert result.tzinfo == UTC
        assert result.hour == 17  # 12 + 5 hours = 17:00 UTC


class TestParseDatetime:
    """Tests for parse_datetime function."""

    def test_none_returns_none(self):
        """parse_datetime should return None for None input."""
        assert parse_datetime(None) is None

    def test_datetime_object_returns_as_is(self):
        """parse_datetime should return datetime object as-is (ensured UTC)."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = parse_datetime(dt)

        assert result == dt
        assert result.tzinfo == UTC

    def test_iso_string_with_z_suffix(self):
        """parse_datetime should parse ISO string with Z suffix."""
        result = parse_datetime("2024-01-01T12:00:00Z")

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 12
        assert result.tzinfo == UTC

    def test_iso_string_with_timezone_offset(self):
        """parse_datetime should parse ISO string with timezone offset."""
        result = parse_datetime("2024-01-01T12:00:00+00:00")

        assert result is not None
        assert result.tzinfo == UTC

    def test_iso_string_naive_assumes_utc(self):
        """parse_datetime should assume UTC for naive ISO strings."""
        result = parse_datetime("2024-01-01T12:00:00")

        assert result is not None
        assert result.tzinfo == UTC

    def test_iso_string_with_microseconds(self):
        """parse_datetime should handle microseconds."""
        result = parse_datetime("2024-01-01T12:00:00.123456Z")

        assert result is not None
        assert result.microsecond == 123456

    def test_invalid_string_raises_value_error(self):
        """parse_datetime should raise ValueError for invalid strings."""
        with pytest.raises(ValueError, match="Could not parse datetime string"):
            parse_datetime("not a date")

    def test_invalid_type_raises_type_error(self):
        """parse_datetime should raise TypeError for invalid types."""
        with pytest.raises(TypeError):
            parse_datetime(123)


class TestFormatDatetime:
    """Tests for format_datetime function."""

    def test_none_returns_none(self):
        """format_datetime should return None for None input."""
        assert format_datetime(None) is None

    def test_iso_format_default(self):
        """format_datetime should use ISO format by default."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = format_datetime(dt)

        assert result == "2024-01-01T12:00:00Z"

    def test_iso_format_explicit(self):
        """format_datetime should format with ISO format."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = format_datetime(dt, "iso")

        assert result == "2024-01-01T12:00:00Z"

    def test_iso_format_with_microseconds(self):
        """format_datetime should handle microseconds in ISO format."""
        dt = datetime(2024, 1, 1, 12, 0, 0, 123456, tzinfo=UTC)
        result = format_datetime(dt, "iso")

        assert "2024-01-01T12:00:00" in result
        assert result.endswith("Z")

    def test_human_format(self):
        """format_datetime should format with human-readable format."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = format_datetime(dt, "human")

        assert result == "2024-01-01 12:00:00 UTC"

    def test_date_format(self):
        """format_datetime should format with date-only format."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = format_datetime(dt, "date")

        assert result == "2024-01-01"

    def test_invalid_format_raises_value_error(self):
        """format_datetime should raise ValueError for invalid format."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match="Unknown format"):
            format_datetime(dt, "invalid")

    def test_converts_to_utc(self):
        """format_datetime should convert non-UTC datetimes to UTC."""
        est = timezone(timedelta(hours=-5))
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=est)
        result = format_datetime(dt, "iso")

        # Should be 17:00 UTC (12 + 5 hours)
        assert result == "2024-01-01T17:00:00Z"
