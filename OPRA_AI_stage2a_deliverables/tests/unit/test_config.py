"""Unit tests for ``opra.core.config`` and ``opra.core.exceptions``."""

from dataclasses import FrozenInstanceError, fields

import pytest

from opra.core.config import (
    DEFAULT_MATURITY_BUFFER_DAYS,
    DEFAULT_MAX_ROWS,
    DEFAULT_MAX_UPLOAD_BYTES,
    DEFAULT_MIN_SAMPLE_SIZE,
    ConfigSnapshot,
    OpraConfig,
)
from opra.core.exceptions import ConfigurationError, OpraError

SETTING_NAMES = ("max_upload_bytes", "max_rows", "maturity_buffer_days", "min_sample_size")
VALID = {
    "max_upload_bytes": 1,
    "max_rows": 1,
    "maturity_buffer_days": 0,
    "min_sample_size": 1,
}
# Smallest valid value per setting; one below it must be rejected.
MINIMUM = {"max_upload_bytes": 1, "max_rows": 1, "maturity_buffer_days": 0, "min_sample_size": 1}


def test_exception_hierarchy() -> None:
    assert issubclass(ConfigurationError, OpraError)
    assert issubclass(OpraError, Exception)


def test_defaults_match_approved_values() -> None:
    config = OpraConfig()
    assert config.max_upload_bytes == 10 * 1024 * 1024 == DEFAULT_MAX_UPLOAD_BYTES
    assert config.max_rows == 100_000 == DEFAULT_MAX_ROWS
    assert config.maturity_buffer_days == 3 == DEFAULT_MATURITY_BUFFER_DAYS
    assert config.min_sample_size == 10 == DEFAULT_MIN_SAMPLE_SIZE


def test_custom_values_are_accepted() -> None:
    config = OpraConfig(max_upload_bytes=5, max_rows=7, maturity_buffer_days=2, min_sample_size=4)
    assert (config.max_upload_bytes, config.max_rows) == (5, 7)
    assert (config.maturity_buffer_days, config.min_sample_size) == (2, 4)


@pytest.mark.parametrize("name", SETTING_NAMES)
def test_minimum_boundary_is_accepted(name: str) -> None:
    config = OpraConfig(**{name: MINIMUM[name]})
    assert getattr(config, name) == MINIMUM[name]


@pytest.mark.parametrize("name", SETTING_NAMES)
@pytest.mark.parametrize("offset", [1, 1000])
def test_below_minimum_is_rejected(name: str, offset: int) -> None:
    with pytest.raises(ConfigurationError, match=name):
        OpraConfig(**{name: MINIMUM[name] - offset})


def test_zero_is_valid_only_for_maturity_buffer() -> None:
    assert OpraConfig(maturity_buffer_days=0).maturity_buffer_days == 0
    for name in ("max_upload_bytes", "max_rows", "min_sample_size"):
        with pytest.raises(ConfigurationError):
            OpraConfig(**{name: 0})


@pytest.mark.parametrize("name", SETTING_NAMES)
@pytest.mark.parametrize("bad", [True, False, 1.0, 3.5, "10", None, b"1", [1]])
def test_non_integer_types_are_rejected_not_coerced(name: str, bad: object) -> None:
    with pytest.raises(ConfigurationError, match=f"{name} must be an integer"):
        OpraConfig(**{name: bad})


def test_error_for_wrong_type_does_not_echo_value() -> None:
    with pytest.raises(ConfigurationError) as info:
        OpraConfig(max_rows="secret-looking-value")  # type: ignore[arg-type]
    assert "secret-looking-value" not in str(info.value)
    assert "str" in str(info.value)


def test_invalid_value_is_never_clamped_or_defaulted() -> None:
    with pytest.raises(ConfigurationError):
        OpraConfig(max_rows=-5)


def test_config_is_frozen() -> None:
    config = OpraConfig()
    with pytest.raises(FrozenInstanceError):
        config.max_rows = 1  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        config.extra = 1  # type: ignore[attr-defined]


def test_snapshot_reflects_config_values() -> None:
    config = OpraConfig(max_upload_bytes=9, max_rows=8, maturity_buffer_days=0, min_sample_size=2)
    snapshot = config.snapshot()
    assert isinstance(snapshot, ConfigSnapshot)
    for name in SETTING_NAMES:
        assert getattr(snapshot, name) == getattr(config, name)


def test_snapshot_has_exactly_the_four_approved_settings() -> None:
    assert tuple(f.name for f in fields(ConfigSnapshot)) == SETTING_NAMES


def test_snapshot_is_deterministic_equal_and_hashable() -> None:
    first = OpraConfig().snapshot()
    second = OpraConfig().snapshot()
    assert first == second
    assert hash(first) == hash(second)
    assert first != OpraConfig(min_sample_size=11).snapshot()
    assert len({first, second}) == 1


def test_snapshot_is_frozen() -> None:
    snapshot = OpraConfig().snapshot()
    with pytest.raises(FrozenInstanceError):
        snapshot.max_rows = 1  # type: ignore[misc]


def test_snapshot_unaffected_by_later_config_construction() -> None:
    snapshot = OpraConfig().snapshot()
    OpraConfig(max_rows=1)  # a different config must not alter an existing snapshot
    assert snapshot.max_rows == DEFAULT_MAX_ROWS


@pytest.mark.parametrize("name", SETTING_NAMES)
def test_snapshot_validates_on_direct_construction(name: str) -> None:
    with pytest.raises(ConfigurationError, match=name):
        ConfigSnapshot(**{**VALID, name: MINIMUM[name] - 1})
    with pytest.raises(ConfigurationError, match=f"{name} must be an integer"):
        ConfigSnapshot(**{**VALID, name: 1.5})


def test_snapshot_requires_all_settings() -> None:
    with pytest.raises(TypeError):
        ConfigSnapshot(max_upload_bytes=1)  # type: ignore[call-arg]
