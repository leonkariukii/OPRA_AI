"""Unit tests for ``opra.models.analytics`` (decisions D-03, D-05, D-06 and D-11)."""

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction

import pytest

from opra.core.exceptions import ModelValidationError, OpraError
from opra.models.analytics import MetricResult, MetricStatus, MetricValue
from opra.models.periods import ReportingPeriod

PERIOD = ReportingPeriod(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 2, 1, tzinfo=UTC))
OTHER_PERIOD = ReportingPeriod(datetime(2026, 2, 1, tzinfo=UTC), datetime(2026, 3, 1, tzinfo=UTC))

FINITE_VALUES = [Decimal(1), Decimal(0), Decimal("-3.5"), Decimal("1E+3")]
NON_FINITE_VALUES = [
    Decimal("NaN"),
    Decimal("-NaN"),
    Decimal("sNaN"),
    Decimal("Infinity"),
    Decimal("-Infinity"),
]
NON_DECIMAL_VALUES = [
    True,
    False,
    0,
    1,
    -1,
    0.0,
    1.5,
    float("nan"),
    float("inf"),
    "1",
    "Decimal('1')",
    b"1",
    Fraction(1, 2),
    [Decimal(1)],
]
NON_AVAILABLE = [MetricStatus.UNAVAILABLE, MetricStatus.NOT_APPLICABLE]


# --- MetricStatus ------------------------------------------------------------------------


def test_metric_status_members_and_values() -> None:
    assert [(m.name, m.value) for m in MetricStatus] == [
        ("AVAILABLE", "available"),
        ("UNAVAILABLE", "unavailable"),
        ("NOT_APPLICABLE", "not_applicable"),
    ]


def test_metric_status_is_not_a_string_and_does_not_equal_strings() -> None:
    assert not isinstance(MetricStatus.AVAILABLE, str)
    assert MetricStatus.AVAILABLE != "available"
    assert MetricStatus.AVAILABLE != "AVAILABLE"


# --- MetricValue: valid combinations -----------------------------------------------------


@pytest.mark.parametrize("value", FINITE_VALUES)
def test_available_with_finite_decimal_is_valid(value: Decimal) -> None:
    metric_value = MetricValue(MetricStatus.AVAILABLE, value)
    assert metric_value.status is MetricStatus.AVAILABLE
    assert metric_value.value == value


@pytest.mark.parametrize("status", NON_AVAILABLE)
def test_non_available_statuses_with_none_are_valid(status: MetricStatus) -> None:
    metric_value = MetricValue(status, None)
    assert metric_value.status is status
    assert metric_value.value is None


@pytest.mark.parametrize("status", NON_AVAILABLE)
def test_value_defaults_to_none(status: MetricStatus) -> None:
    assert MetricValue(status).value is None
    assert MetricValue(status) == MetricValue(status, None)


def test_fields_are_status_then_value() -> None:
    assert [f.name for f in fields(MetricValue)] == ["status", "value"]
    assert fields(MetricValue)[1].default is None


def test_keyword_construction() -> None:
    assert MetricValue(status=MetricStatus.AVAILABLE, value=Decimal(2)).value == Decimal(2)


# --- MetricValue: invalid combinations ---------------------------------------------------


def test_available_with_none_is_rejected() -> None:
    with pytest.raises(ModelValidationError, match="value is required when status is AVAILABLE"):
        MetricValue(MetricStatus.AVAILABLE, None)


def test_available_without_value_argument_is_rejected() -> None:
    with pytest.raises(ModelValidationError, match="value is required when status is AVAILABLE"):
        MetricValue(MetricStatus.AVAILABLE)


@pytest.mark.parametrize("status", NON_AVAILABLE)
@pytest.mark.parametrize("value", FINITE_VALUES)
def test_non_available_status_with_decimal_is_rejected(
    status: MetricStatus, value: Decimal
) -> None:
    with pytest.raises(
        ModelValidationError, match=f"value must be None when status is {status.name}"
    ):
        MetricValue(status, value)


@pytest.mark.parametrize("status", NON_AVAILABLE)
def test_zero_is_not_accepted_for_non_available_statuses(status: MetricStatus) -> None:
    with pytest.raises(ModelValidationError, match="value must be None"):
        MetricValue(status, Decimal(0))


# --- MetricValue: strict Decimal rules ---------------------------------------------------


@pytest.mark.parametrize("status", list(MetricStatus))
@pytest.mark.parametrize("bad", NON_DECIMAL_VALUES)
def test_non_decimal_values_are_rejected_for_every_status(
    status: MetricStatus, bad: object
) -> None:
    with pytest.raises(
        ModelValidationError, match=f"value must be a Decimal or None, got {type(bad).__name__}"
    ):
        MetricValue(status, bad)  # type: ignore[arg-type]


def test_bool_int_float_and_str_are_specifically_rejected() -> None:
    for bad in (True, 1, 1.5, "1"):
        with pytest.raises(ModelValidationError, match="must be a Decimal or None"):
            MetricValue(MetricStatus.AVAILABLE, bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("status", list(MetricStatus))
@pytest.mark.parametrize("bad", NON_FINITE_VALUES)
def test_non_finite_decimals_are_rejected_for_every_status(
    status: MetricStatus, bad: Decimal
) -> None:
    with pytest.raises(ModelValidationError, match="value must be finite"):
        MetricValue(status, bad)


def test_wrong_type_error_does_not_echo_the_value() -> None:
    with pytest.raises(ModelValidationError) as info:
        MetricValue(MetricStatus.AVAILABLE, "secret-looking-value")  # type: ignore[arg-type]
    assert "secret-looking-value" not in str(info.value)


@pytest.mark.parametrize("bad", ["AVAILABLE", "available", 1, None, True, Decimal(1)])
def test_status_must_be_a_metric_status(bad: object) -> None:
    with pytest.raises(
        ModelValidationError, match=f"status must be a MetricStatus, got {type(bad).__name__}"
    ):
        MetricValue(bad, Decimal(1))  # type: ignore[arg-type]


def test_status_is_validated_before_value() -> None:
    with pytest.raises(ModelValidationError, match="status must be a MetricStatus"):
        MetricValue("AVAILABLE", 1.5)  # type: ignore[arg-type]


def test_type_is_validated_before_status_value_consistency() -> None:
    with pytest.raises(ModelValidationError, match="must be a Decimal or None"):
        MetricValue(MetricStatus.UNAVAILABLE, 1.5)  # type: ignore[arg-type]


def test_validation_errors_are_domain_errors() -> None:
    with pytest.raises(OpraError):
        MetricValue(MetricStatus.AVAILABLE, None)


# --- MetricValue: zero, precision, object preservation -----------------------------------


@pytest.mark.parametrize("zero", [Decimal(0), Decimal("0.00"), Decimal("-0"), Decimal("0E+5")])
def test_decimal_zero_is_a_valid_available_value(zero: Decimal) -> None:
    metric_value = MetricValue(MetricStatus.AVAILABLE, zero)
    assert metric_value.value is not None
    assert metric_value.value == 0


def test_zero_is_distinct_from_unavailable_and_not_applicable() -> None:
    zero = MetricValue(MetricStatus.AVAILABLE, Decimal(0))
    unavailable = MetricValue(MetricStatus.UNAVAILABLE)
    not_applicable = MetricValue(MetricStatus.NOT_APPLICABLE)
    assert zero.value is not None
    assert unavailable.value is None
    assert not_applicable.value is None
    assert len({zero, unavailable, not_applicable}) == 3
    assert zero != unavailable
    assert zero != not_applicable
    assert unavailable != not_applicable


def test_decimal_object_is_preserved_exactly() -> None:
    original = Decimal("1.2300")
    metric_value = MetricValue(MetricStatus.AVAILABLE, original)
    assert metric_value.value is original


@pytest.mark.parametrize(
    "text",
    ["1.2300", "100", "1E+3", "-0", "0.000000", "12345678901234567890123456789012345.678901"],
)
def test_scale_sign_and_digits_are_preserved(text: str) -> None:
    original = Decimal(text)
    stored = MetricValue(MetricStatus.AVAILABLE, original).value
    assert stored is not None
    assert str(stored) == text
    assert stored.as_tuple() == original.as_tuple()


def test_precision_beyond_default_context_is_preserved() -> None:
    digits = "1." + "1234567890" * 6  # 61 significant digits, more than the default 28
    stored = MetricValue(MetricStatus.AVAILABLE, Decimal(digits)).value
    assert stored is not None
    assert str(stored) == digits


def test_no_quantization_or_float_conversion_occurs() -> None:
    original = Decimal("0.1") + Decimal("0.2")
    stored = MetricValue(MetricStatus.AVAILABLE, original).value
    assert stored == Decimal("0.3")
    assert stored is not None
    assert float(stored) == 0.3  # observing only; the stored value stays a Decimal
    assert isinstance(stored, Decimal)


# --- MetricValue: equality, hashing, immutability ----------------------------------------


def test_equal_metric_values_are_equal_and_hash_equal() -> None:
    first = MetricValue(MetricStatus.AVAILABLE, Decimal("2.5"))
    second = MetricValue(MetricStatus.AVAILABLE, Decimal("2.5"))
    assert first == second
    assert hash(first) == hash(second)


def test_different_status_or_value_are_not_equal() -> None:
    base = MetricValue(MetricStatus.AVAILABLE, Decimal("2.5"))
    assert base != MetricValue(MetricStatus.AVAILABLE, Decimal("2.6"))
    assert base != MetricValue(MetricStatus.UNAVAILABLE)


def test_equality_is_numeric_not_representational() -> None:
    # Pins current behavior: Decimal compares by numeric value, so differing scale is equal.
    first = MetricValue(MetricStatus.AVAILABLE, Decimal("1.0"))
    second = MetricValue(MetricStatus.AVAILABLE, Decimal("1.00"))
    assert first == second
    assert hash(first) == hash(second)
    assert first.value is not None
    assert second.value is not None
    assert str(first.value) != str(second.value)


def test_metric_value_is_frozen() -> None:
    metric_value = MetricValue(MetricStatus.AVAILABLE, Decimal(1))
    with pytest.raises(FrozenInstanceError):
        metric_value.value = Decimal(2)  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        metric_value.status = MetricStatus.UNAVAILABLE  # type: ignore[misc]
    assert metric_value.value == Decimal(1)


def test_metric_value_rejects_new_attributes() -> None:
    metric_value = MetricValue(MetricStatus.UNAVAILABLE)
    # Python 3.11 raises TypeError and later versions AttributeError for unknown names on
    # frozen slotted dataclasses; both reject the assignment.
    with pytest.raises((AttributeError, TypeError)):
        metric_value.extra = 1  # type: ignore[attr-defined]
    assert not hasattr(metric_value, "__dict__")


def test_replace_revalidates_metric_value() -> None:
    available = MetricValue(MetricStatus.AVAILABLE, Decimal(1))
    with pytest.raises(ModelValidationError):
        replace(available, status=MetricStatus.UNAVAILABLE)
    with pytest.raises(ModelValidationError):
        replace(available, value=None)
    assert replace(available, value=Decimal(2)).value == Decimal(2)


# --- MetricResult: valid construction ----------------------------------------------------


@pytest.fixture
def metric_value() -> MetricValue:
    return MetricValue(MetricStatus.AVAILABLE, Decimal("12.50"))


def test_valid_result_keeps_all_fields(metric_value: MetricValue) -> None:
    result = MetricResult("metric-a", metric_value, PERIOD)
    assert result.metric_id == "metric-a"
    assert result.metric_value is metric_value
    assert result.period is PERIOD


def test_result_fields_are_exactly_the_approved_set_in_order() -> None:
    assert [f.name for f in fields(MetricResult)] == ["metric_id", "metric_value", "period"]


def test_result_keyword_construction(metric_value: MetricValue) -> None:
    result = MetricResult(metric_id="m", metric_value=metric_value, period=PERIOD)
    assert result.metric_id == "m"


@pytest.mark.parametrize("status", NON_AVAILABLE)
def test_result_accepts_non_available_metric_values(status: MetricStatus) -> None:
    result = MetricResult("m", MetricValue(status), PERIOD)
    assert result.metric_value.value is None


def test_all_fields_are_required(metric_value: MetricValue) -> None:
    with pytest.raises(TypeError):
        MetricResult("m", metric_value)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        MetricResult()  # type: ignore[call-arg]


# --- MetricResult: metric_id -------------------------------------------------------------


@pytest.mark.parametrize(
    "metric_id",
    ["m", "  padded  ", "\tTabbed", "trailing\n", "a b", "KPI/α-β", "x" * 10_000, "0", "None"],
)
def test_metric_id_is_preserved_exactly(metric_id: str, metric_value: MetricValue) -> None:
    result = MetricResult(metric_id, metric_value, PERIOD)
    assert result.metric_id == metric_id
    assert result.metric_id is metric_id


@pytest.mark.parametrize("metric_id", ["", " ", "   ", "\t", "\n", " \t\r\n ", " ", " "])
def test_empty_or_whitespace_only_metric_id_is_rejected(
    metric_id: str, metric_value: MetricValue
) -> None:
    with pytest.raises(
        ModelValidationError, match="metric_id must not be empty or whitespace-only"
    ):
        MetricResult(metric_id, metric_value, PERIOD)


@pytest.mark.parametrize("bad", [None, 1, 1.5, True, b"metric", ("m",), ["m"], Decimal(1)])
def test_non_string_metric_id_is_rejected(bad: object, metric_value: MetricValue) -> None:
    with pytest.raises(
        ModelValidationError, match=f"metric_id must be a string, got {type(bad).__name__}"
    ):
        MetricResult(bad, metric_value, PERIOD)  # type: ignore[arg-type]


# --- MetricResult: metric_value and period validation ------------------------------------


@pytest.mark.parametrize(
    "bad", [None, Decimal(1), 1, "available", (MetricStatus.AVAILABLE, Decimal(1)), {}]
)
def test_metric_value_must_be_a_metric_value(bad: object) -> None:
    with pytest.raises(
        ModelValidationError, match=f"metric_value must be a MetricValue, got {type(bad).__name__}"
    ):
        MetricResult("m", bad, PERIOD)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "2026-01",
        1,
        (datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 2, 1, tzinfo=UTC)),
        {"start_utc": datetime(2026, 1, 1, tzinfo=UTC)},
        datetime(2026, 1, 1, tzinfo=UTC),
    ],
)
def test_period_must_be_a_reporting_period(bad: object, metric_value: MetricValue) -> None:
    with pytest.raises(
        ModelValidationError, match=f"period must be a ReportingPeriod, got {type(bad).__name__}"
    ):
        MetricResult("m", metric_value, bad)  # type: ignore[arg-type]


def test_result_validation_order(metric_value: MetricValue) -> None:
    with pytest.raises(ModelValidationError, match="metric_id must be a string"):
        MetricResult(None, None, None)  # type: ignore[arg-type]
    with pytest.raises(ModelValidationError, match="metric_value must be a MetricValue"):
        MetricResult("m", None, None)  # type: ignore[arg-type]
    with pytest.raises(ModelValidationError, match="period must be a ReportingPeriod"):
        MetricResult("m", metric_value, None)  # type: ignore[arg-type]


def test_result_errors_are_domain_errors(metric_value: MetricValue) -> None:
    with pytest.raises(OpraError):
        MetricResult("", metric_value, PERIOD)


# --- MetricResult: equality, hashing, immutability ---------------------------------------


def test_equal_results_are_equal_and_hash_equal(metric_value: MetricValue) -> None:
    first = MetricResult("m", metric_value, PERIOD)
    second = MetricResult("m", MetricValue(MetricStatus.AVAILABLE, Decimal("12.50")), PERIOD)
    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second}) == 1


def test_results_differing_in_any_field_are_not_equal(metric_value: MetricValue) -> None:
    base = MetricResult("m", metric_value, PERIOD)
    assert base != MetricResult("other", metric_value, PERIOD)
    assert base != MetricResult("m", MetricValue(MetricStatus.UNAVAILABLE), PERIOD)
    assert base != MetricResult("m", metric_value, OTHER_PERIOD)
    assert base != MetricResult(" m", metric_value, PERIOD)


def test_result_equality_uses_period_instants(metric_value: MetricValue) -> None:
    plus_3 = timezone(timedelta(hours=3))
    same_instants = ReportingPeriod(
        datetime(2026, 1, 1, 3, 0, tzinfo=plus_3), datetime(2026, 2, 1, 3, 0, tzinfo=plus_3)
    )
    first = MetricResult("m", metric_value, PERIOD)
    second = MetricResult("m", metric_value, same_instants)
    assert first == second
    assert hash(first) == hash(second)


def test_result_is_frozen(metric_value: MetricValue) -> None:
    result = MetricResult("m", metric_value, PERIOD)
    with pytest.raises(FrozenInstanceError):
        result.metric_id = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.metric_value = MetricValue(MetricStatus.UNAVAILABLE)  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.period = OTHER_PERIOD  # type: ignore[misc]
    assert result.metric_id == "m"
    assert result.metric_value is metric_value
    assert result.period is PERIOD


def test_result_rejects_new_attributes(metric_value: MetricValue) -> None:
    result = MetricResult("m", metric_value, PERIOD)
    with pytest.raises((AttributeError, TypeError)):
        result.extra = 1  # type: ignore[attr-defined]
    assert not hasattr(result, "__dict__")


def test_replace_revalidates_result(metric_value: MetricValue) -> None:
    result = MetricResult("m", metric_value, PERIOD)
    assert replace(result, period=OTHER_PERIOD).period is OTHER_PERIOD
    assert result.period is PERIOD
    with pytest.raises(ModelValidationError):
        replace(result, metric_id="  ")
    with pytest.raises(ModelValidationError):
        replace(result, period=None)


def test_nested_values_are_immutable(metric_value: MetricValue) -> None:
    result = MetricResult("m", metric_value, PERIOD)
    with pytest.raises(FrozenInstanceError):
        result.metric_value.value = Decimal(0)  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.period.end_utc = datetime(2030, 1, 1, tzinfo=UTC)  # type: ignore[misc]
