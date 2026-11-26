"""Tests for the OPRA domain exception hierarchy."""

from opra.core.exceptions import ConfigurationError, ModelValidationError, OpraError


def test_model_validation_error_inherits_directly_from_opra_error() -> None:
    assert ModelValidationError.__bases__ == (OpraError,)
    assert issubclass(ModelValidationError, Exception)
    assert not issubclass(ModelValidationError, ConfigurationError)
