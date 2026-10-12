"""The partner adapter contract.

Every external provider — clearing firm, sponsor bank, and the simulator — implements
these four operations and nothing else. Domain code sees domain types; a partner's
field names never appear past this boundary.

Idempotency keys are derived from our own aggregate ids and versions, never generated
randomly, so a retry after an ambiguous timeout refers to the same instruction rather
than creating a second one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol, Sequence

from guild.shared.money import Money, Quantity


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class PlacementStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    #: The call timed out without a definitive answer. The order may or may not exist.
    #: Never retried blindly — query by idempotency key, reconcile, then decide.
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class BlockOrder:
    """One instruction for a whole batch, carrying its sealed allocation."""

    idempotency_key: str
    instrument: str
    side: Side
    quantity: Quantity
    account_ids: Sequence[str]


@dataclass(frozen=True, slots=True)
class Placement:
    status: PlacementStatus
    partner_order_id: str | None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class PositionRow:
    account_id: str
    instrument: str
    quantity: Quantity
    as_of: datetime


@dataclass(frozen=True, slots=True)
class CashRow:
    account_id: str
    available: Money
    as_of: datetime


@dataclass(frozen=True, slots=True)
class ReconciliationFile:
    """A partner's authoritative snapshot for a period.

    Immutable by nature, which is why reconciliation never needs to replay these —
    only our own derived state does.
    """

    period_end: datetime
    positions: Sequence[PositionRow]
    cash: Sequence[CashRow]


class PartnerAdapter(Protocol):
    """Four methods. A real integration and the simulator are interchangeable."""

    name: str

    async def place(self, order: BlockOrder) -> Placement: ...

    async def cancel(self, idempotency_key: str) -> bool: ...

    async def positions(self, account_ids: Sequence[str]) -> Sequence[PositionRow]: ...

    async def reconcile(self, period_end: datetime) -> ReconciliationFile: ...
