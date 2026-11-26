"""Domain exception hierarchy for OPRA.AI.

All OPRA domain errors inherit from :class:`OpraError`. Messages must be actionable and
non-sensitive: they must never include raw CSV rows or customer/vehicle identifiers.
"""


class OpraError(Exception):
    """Base class for all OPRA.AI domain errors."""


class ConfigurationError(OpraError):
    """Raised when a configuration value is invalid.

    Configuration is validated fail-fast: invalid values are never clamped or replaced
    with defaults.
    """
