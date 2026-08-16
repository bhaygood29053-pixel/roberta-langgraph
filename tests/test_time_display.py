"""Tests for deterministic user-facing UTC timestamp display."""

from roberta.time_utils import format_observed_at_utc


def test_iso_timestamp_is_rendered_as_date_and_utc_time() -> None:
    assert (
        format_observed_at_utc("2026-08-15T23:37:12.909297Z")
        == "2026-08-15 | 23:37:12 UTC"
    )


def test_offset_timestamp_is_converted_to_utc_for_display() -> None:
    assert (
        format_observed_at_utc("2026-08-15T19:37:12-04:00")
        == "2026-08-15 | 23:37:12 UTC"
    )


def test_naive_or_invalid_timestamp_is_not_labeled_utc() -> None:
    assert format_observed_at_utc("2026-08-15T23:37:12") is None
    assert format_observed_at_utc("not-a-time") is None
