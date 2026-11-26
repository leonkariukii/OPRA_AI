"""Unit tests for ``ModelValidationError`` and its relationship to existing exceptions."""

import pytest

from opra.core.exceptions import ConfigurationError, ModelValidationError, OpraError


def test_model_validation_error_subclasses_opra_error() -> None:
    assert issubclass(ModelValidationError, OpraError)
    assert issubclass(ModelValidationError, Exception)


def test_model_validation_error_is_not_a_builtin_value_or_type_error() -> None:
    assert not issubclass(ModelValidationError, (ValueError, TypeError))


def test_configuration_error_hierarchy_is_unchanged() -> None:
    assert issubclass(ConfigurationError, OpraError)
    assert ConfigurationError.__bases__ == (OpraError,)


def test_model_validation_and_configuration_errors_are_distinct_siblings() -> None:
    assert not issubclass(ModelValidationError, ConfigurationError)
    assert not issubclass(ConfigurationError, ModelValidationError)
    assert ModelValidationError.__bases__ == (OpraError,)


def test_model_validation_error_instance_is_opra_error_but_not_configuration_error() -> None:
    error = ModelValidationError("invalid model")
    assert isinstance(error, OpraError)
    assert not isinstance(error, ConfigurationError)


def test_configuration_error_instance_is_not_model_validation_error() -> None:
    error = ConfigurationError("invalid configuration")
    assert isinstance(error, OpraError)
    assert not isinstance(error, ModelValidationError)


def test_model_validation_error_can_be_raised_and_caught_as_opra_error() -> None:
    with pytest.raises(OpraError) as info:
        raise ModelValidationError("invalid model")
    assert type(info.value) is ModelValidationError


def test_model_validation_error_preserves_message() -> None:
    assert str(ModelValidationError("value must be finite.")) == "value must be finite."
