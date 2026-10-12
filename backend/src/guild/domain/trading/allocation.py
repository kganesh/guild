"""Average-price allocation across a batch.

This module is the executable form of ADR 0003. Two properties must hold:

1. Every account in a batch is booked at the *same* volume-weighted average price.
2. The allocated quantities sum exactly to the filled quantity. No share is created or
   lost in rounding, and the remainder is absorbed by the firm rather than by whichever
   member happens to round last.

The allocation statement is sealed *before* the order is submitted. Allocating after
seeing fills would allow good prices to be steered between accounts, which is precisely
what a pre-trade statement exists to prevent.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Sequence

from guild.shared.money import Price, Quantity, QTY_PRECISION


@dataclass(frozen=True, slots=True)
class Fill:
    """One execution against a block order."""

    quantity: Quantity
    price: Price


@dataclass(frozen=True, slots=True)
class AllocationLine:
    """One account's intended share, fixed before submission."""

    account_id: str
    quantity: Quantity


@dataclass(frozen=True, slots=True)
class AllocationStatement:
    """Sealed pre-trade intent: who gets what, before anything is submitted."""

    batch_id: str
    instrument: str
    lines: Sequence[AllocationLine]

    @property
    def total(self) -> Quantity:
        total = Decimal("0")
        for line in self.lines:
            total += line.quantity.shares
        return Quantity(total)


@dataclass(frozen=True, slots=True)
class Allocated:
    """The post-trade result: one price for everyone, plus the firm's residual."""

    price: Price
    per_account: Mapping[str, Quantity]
    firm_residual: Quantity


def average_price(fills: Sequence[Fill]) -> Price:
    """Volume-weighted average across every fill in the block."""
    if not fills:
        raise ValueError("no fills to average")
    gross = Decimal("0")
    shares = Decimal("0")
    for fill in fills:
        gross += fill.price.value * fill.quantity.shares
        shares += fill.quantity.shares
    if shares == 0:
        raise ValueError("fills total zero shares")
    return Price(gross / shares)


def allocate(statement: AllocationStatement, fills: Sequence[Fill]) -> Allocated:
    """Allocate filled quantity pro-rata against the sealed statement.

    A full fill gives every account exactly its stated quantity. A partial fill scales
    every account by the same ratio. Rounding is floor-per-account, with the residual
    retained by the firm so the allocated total never exceeds what was filled.
    """
    price = average_price(fills)
    filled = Quantity(sum((f.quantity.shares for f in fills), Decimal("0")))
    intended = statement.total

    if intended.shares <= 0:
        raise ValueError("allocation statement is empty")
    if filled.shares > intended.shares:
        raise ValueError(
            f"filled {filled.shares} exceeds the sealed statement {intended.shares}"
        )

    ratio = filled.shares / intended.shares
    per_account: dict[str, Quantity] = {}
    allocated_total = Decimal("0")

    for line in statement.lines:
        share = (line.quantity.shares * ratio).quantize(QTY_PRECISION, rounding="ROUND_DOWN")
        per_account[line.account_id] = Quantity(share)
        allocated_total += share

    residual = filled.shares - allocated_total
    if residual < 0:  # pragma: no cover - floor rounding cannot overshoot
        raise AssertionError("allocated more than was filled")

    return Allocated(price=price, per_account=per_account, firm_residual=Quantity(residual))
