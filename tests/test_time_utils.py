"""Tests for deterministic timestamp normalization."""

from roberta.time_utils import normalize_observed_at


def test_numeric_epoch_is_normalized_to_canonical_utc_iso() -> None:
    assert (
        normalize_observed_at(1786835050.0581603)
        == "2026-08-15T23:04:10.058160Z"
    )


def test_existing_string_timestamp_is_preserved_verbatim() -> None:
    value = "2026-08-15T21:45:00Z"
    assert normalize_observed_at(value) == value


def test_invalid_or_unsupported_timestamp_is_not_guessed() -> None:
    assert normalize_observed_at(None) is None
    assert normalize_observed_at("") is None
    assert normalize_observed_at(float("nan")) is None
    assert normalize_observed_at(True) is None
    assert normalize_observed_at({"epoch": 1786835050}) is None
