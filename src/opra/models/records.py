"""Immutable canonical raw automotive job records."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from opra.core.exceptions import ModelValidationError


class JobStatus(str, Enum):
    """Canonical job lifecycle status."""

    COMPLETED = "completed"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"


CanonicalStatus = JobStatus


ISO_4217_CODES = frozenset(
    "AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND "
    "BOB BOV BRL BSD BTN BWP BYN BZD CAD CDF CHE CHF CHW CLF CLP CNH CNY COP COU "
    "CRC CUC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP GEL GHS GIP "
    "GMD GNF GTQ GYD HKD HNL HTG HUF IDR ILS INR IQD IRR ISK JMD JOD JPY KES "
    "KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL LYD MAD MDL MGA MKD "
    "MMK MNT MOP MRU MUR MVR MWK MXN MXV MYR MZN NAD NGN NIO NOK NPR NZD OMR "
    "PAB PEN PGK PHP PKR PLN PYG QAR RON RSD RUB RWF SAR SBD SCR SDG SEK SGD "
    "SHP SLE SLL SOS SRD SSP STN SVC SYP SZL THB TJS TMT TND TOP TRY TTD TWD "
    "TZS UAH UGX USD USN UYI UYU UYW UZS VED VES VND VUV WST XAF XAG XAU XBA "
    "XBB XBC XBD XCD XDR XOF XPD XPF XPT XSU XTS XUA XXX YER ZAR ZMW ZWG"
    .split()
)


def _utc_datetime(name: str, value: object, *, optional: bool = False) -> datetime | None:
    if optional and value is None:
        return None
    if not isinstance(value, datetime):
        raise ModelValidationError(f"{name} must be a datetime.")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ModelValidationError(f"{name} must have an explicit UTC offset.")
        return value.astimezone(UTC)
    except (ValueError, OverflowError):
        raise ModelValidationError(f"{name} cannot be normalized to UTC.") from None


@dataclass(frozen=True, slots=True)
class JobRecord:
    """Normalized source job record; contains no derived analytics or period assignment."""

    job_id: str
    status: JobStatus
    opened_at: datetime
    completed_at: datetime | None = None
    billed_amount: Decimal | None = None
    billed_currency: str | None = None
    paid_amount: Decimal | None = None
    paid_currency: str | None = None
    estimated_amount: Decimal | None = None
    estimated_currency: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise ModelValidationError("job_id must be a non-empty string.")
        if not isinstance(self.status, JobStatus):
            raise ModelValidationError("status must be a canonical JobStatus.")
        object.__setattr__(self, "opened_at", _utc_datetime("opened_at", self.opened_at))
        object.__setattr__(self, "completed_at", _utc_datetime("completed_at", self.completed_at, optional=True))
        for amount_name, currency_name in (
            ("billed_amount", "billed_currency"),
            ("paid_amount", "paid_currency"),
            ("estimated_amount", "estimated_currency"),
        ):
            amount = getattr(self, amount_name)
            currency = getattr(self, currency_name)
            if amount is None:
                if currency is not None:
                    raise ModelValidationError(f"{currency_name} requires its amount.")
                continue
            if not isinstance(amount, Decimal) or not amount.is_finite():
                raise ModelValidationError(f"{amount_name} must be a finite Decimal.")
            if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha() or not currency.isupper():
                raise ModelValidationError(f"{currency_name} must be an ISO 4217 alphabetic code.")
            if currency not in ISO_4217_CODES:
                raise ModelValidationError(f"{currency_name} must be an ISO 4217 code.")


RawJobRecord = JobRecord

