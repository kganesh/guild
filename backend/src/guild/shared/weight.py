"""Portfolio weights as integer basis points.

A Guild strategy is a set of target weights that must total exactly 100%. Expressed as
floats they do not reliably total 1.0; expressed as integer basis points they total
exactly 10,000 or the construction fails. There is no third option worth having.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

BASIS_POINTS_TOTAL = 10_000


@dataclass(frozen=True, slots=True)
class Weight:
    """A portfolio weight in basis points. 2,850 bps == 28.50%."""

    basis_points: int

    def __post_init__(self) -> None:
        if isinstance(self.basis_points, float):
            raise TypeError("Weight must not be constructed from float; use basis points")
        if not isinstance(self.basis_points, int):
            raise TypeError(f"basis_points must be int, got {type(self.basis_points).__name__}")
        if not 0 <= self.basis_points <= BASIS_POINTS_TOTAL:
            raise ValueError(f"basis_points out of range: {self.basis_points}")

    @classmethod
    def from_percent(cls, percent: Decimal | int | str) -> "Weight":
        """Build from a percentage. Rejects float, and rejects sub-basis-point precision."""
        if isinstance(percent, float):
            raise TypeError("use Decimal or str, not float")
        value = Decimal(str(percent)) * 100
        if value != value.to_integral_value():
            raise ValueError(f"{percent}% is finer than one basis point")
        return cls(int(value))

    @property
    def fraction(self) -> Decimal:
        return Decimal(self.basis_points) / Decimal(BASIS_POINTS_TOTAL)

    def __str__(self) -> str:
        return f"{Decimal(self.basis_points) / 100}%"


def assert_totals_to_one(weights: Iterable[Weight]) -> None:
    """Raise unless the weights total exactly 100%.

    Called by the Proposal aggregate when validating a proposed change against the
    Guild's mandate. Exactness is the point: a strategy that totals 99.99% is a bug
    that would otherwise surface as a residual cash position nobody voted for.
    """
    total = sum(w.basis_points for w in weights)
    if total != BASIS_POINTS_TOTAL:
        raise ValueError(
            f"weights total {total} basis points, expected {BASIS_POINTS_TOTAL}"
        )
