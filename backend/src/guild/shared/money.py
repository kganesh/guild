"""Money and quantity types.

Python will not stop you doing money arithmetic in floating point, so these types do.
See docs/adr/0006-decimal-money-basis-point-weights.md for why this matters here
specifically: average-price allocation across dozens of accounts is the product's
central fairness claim, and float drift breaks it in the fourth decimal.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union

Numeric = Union[Decimal, int, str]

CENTS = Decimal("0.01")
#: Prices are carried to four decimals: venues quote sub-cent average prices.
PRICE_PRECISION = Decimal("0.0001")
#: Fractional share quantities.
QTY_PRECISION = Decimal("0.000001")


def _to_decimal(value: Numeric, field: str) -> Decimal:
    if isinstance(value, float):
        raise TypeError(
            f"{field} must not be constructed from float "
            f"(got {value!r}); pass Decimal, int or str"
        )
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@dataclass(frozen=True, slots=True)
class Money:
    """An exact amount in a single currency.

    Construction from ``float`` raises. Arithmetic between different currencies raises.
    Money times Money is meaningless and is not implemented.
    """

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", _to_decimal(self.amount, "Money.amount"))

    @classmethod
    def zero(cls, currency: str = "USD") -> "Money":
        return cls(Decimal("0"), currency)

    def _check(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(f"currency mismatch: {self.currency} vs {other.currency}")

    def __add__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Numeric) -> "Money":
        return Money(self.amount * _to_decimal(factor, "factor"), self.currency)

    def __neg__(self) -> "Money":
        return Money(-self.amount, self.currency)

    def __lt__(self, other: "Money") -> bool:
        self._check(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        self._check(other)
        return self.amount <= other.amount

    def quantize_cents(self, rounding: str = ROUND_HALF_UP) -> "Money":
        return Money(self.amount.quantize(CENTS, rounding=rounding), self.currency)

    def is_zero(self) -> bool:
        return self.amount == 0

    def __str__(self) -> str:
        return f"{self.amount.quantize(CENTS)} {self.currency}"


@dataclass(frozen=True, slots=True)
class Price:
    """A per-share price, carried to four decimals."""

    value: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        v = _to_decimal(self.value, "Price.value")
        if v <= 0:
            raise ValueError(f"price must be positive, got {v}")
        object.__setattr__(self, "value", v.quantize(PRICE_PRECISION))

    def times(self, quantity: "Quantity") -> Money:
        return Money(self.value * quantity.shares, self.currency)


@dataclass(frozen=True, slots=True)
class Quantity:
    """A share quantity, fractional to six decimals."""

    shares: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "shares",
            _to_decimal(self.shares, "Quantity.shares").quantize(QTY_PRECISION),
        )

    def __add__(self, other: "Quantity") -> "Quantity":
        return Quantity(self.shares + other.shares)

    def __sub__(self, other: "Quantity") -> "Quantity":
        return Quantity(self.shares - other.shares)

    def is_zero(self) -> bool:
        return self.shares == 0
