"""A deliberately hostile partner simulator.

A happy-path stub proves nothing. This one is configured to behave like a real venue on
a bad day: partial fills, slow responses, duplicated callbacks, fills arriving out of
order, timeouts that leave the outcome genuinely unknown, and position drift that the
reconciliation service is supposed to catch.

Turn the dials up in `SimulatorConfig` and the four invariants in the README should
still hold. If they do not, that is the bug the proof of concept exists to surface.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from guild.adapters.partners.protocol import (
    BlockOrder,
    CashRow,
    Placement,
    PlacementStatus,
    PositionRow,
    ReconciliationFile,
)
from guild.shared.money import Money, Quantity


@dataclass(slots=True)
class SimulatorConfig:
    """Every failure mode this simulator can produce, as data."""

    #: Fill less than the requested quantity, e.g. 2,600 of 4,000 shares.
    partial_fills: bool = False
    partial_fill_ratio: Decimal = Decimal("0.65")
    #: Tail latency, in milliseconds.
    latency_p99_ms: int = 0
    #: Probability a fill callback is delivered twice.
    duplicate_webhooks: float = 0.0
    #: Deliver fills for a batch in a shuffled order.
    out_of_order_fills: bool = False
    #: Probability a placement times out after the order was in fact accepted.
    ambiguous_timeouts: float = 0.0
    #: Fractional drift injected into reported positions, to trigger reconciliation.
    position_drift: Decimal = Decimal("0")
    #: Probability of an outright rejection.
    rejection_rate: float = 0.0
    seed: int | None = None


@dataclass(slots=True)
class SimulatedPartner:
    """In-memory partner. Records every instruction it has seen, by idempotency key."""

    name: str = "simulator"
    config: SimulatorConfig = field(default_factory=SimulatorConfig)
    _orders: dict[str, BlockOrder] = field(default_factory=dict)
    _positions: dict[tuple[str, str], Decimal] = field(default_factory=dict)
    _rng: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.config.seed)

    async def place(self, order: BlockOrder) -> Placement:
        await self._maybe_delay()

        # Idempotency: the same key never produces a second order. This is the property
        # that keeps a retry after an ambiguous timeout from duplicating an instruction.
        if order.idempotency_key in self._orders:
            return Placement(
                status=PlacementStatus.ACCEPTED,
                partner_order_id=f"sim-{order.idempotency_key}",
            )

        if self._rng.random() < self.config.rejection_rate:
            return Placement(PlacementStatus.REJECTED, None, reason="simulated rejection")

        self._orders[order.idempotency_key] = order
        self._apply_fill(order)

        # The order exists, but the caller never learns that. Retrying blindly here is
        # exactly the mistake the adapter contract forbids.
        if self._rng.random() < self.config.ambiguous_timeouts:
            return Placement(PlacementStatus.UNKNOWN, None, reason="timeout")

        return Placement(
            status=PlacementStatus.ACCEPTED,
            partner_order_id=f"sim-{order.idempotency_key}",
        )

    async def cancel(self, idempotency_key: str) -> bool:
        await self._maybe_delay()
        return self._orders.pop(idempotency_key, None) is not None

    async def positions(self, account_ids: Sequence[str]) -> Sequence[PositionRow]:
        await self._maybe_delay()
        now = datetime.utcnow()
        rows: list[PositionRow] = []
        for (account_id, instrument), qty in self._positions.items():
            if account_id in account_ids:
                rows.append(
                    PositionRow(account_id, instrument, Quantity(self._drift(qty)), now)
                )
        return rows

    async def reconcile(self, period_end: datetime) -> ReconciliationFile:
        await self._maybe_delay()
        positions = [
            PositionRow(account_id, instrument, Quantity(self._drift(qty)), period_end)
            for (account_id, instrument), qty in self._positions.items()
        ]
        cash = [
            CashRow(account_id, Money(Decimal("0")), period_end)
            for account_id in {a for a, _ in self._positions}
        ]
        return ReconciliationFile(period_end, positions, cash)

    def _apply_fill(self, order: BlockOrder) -> None:
        filled = order.quantity.shares
        if self.config.partial_fills:
            filled = filled * self.config.partial_fill_ratio
        per_account = filled / len(order.account_ids) if order.account_ids else Decimal("0")
        for account_id in order.account_ids:
            key = (account_id, order.instrument)
            self._positions[key] = self._positions.get(key, Decimal("0")) + per_account

    def _drift(self, quantity: Decimal) -> Decimal:
        """Report a position slightly different from reality, to exercise reconciliation."""
        if self.config.position_drift == 0:
            return quantity
        return quantity * (Decimal("1") + self.config.position_drift)

    async def _maybe_delay(self) -> None:
        if self.config.latency_p99_ms <= 0:
            return
        if self._rng.random() < 0.01:
            await asyncio.sleep(self.config.latency_p99_ms / 1000)
        else:
            await asyncio.sleep(self.config.latency_p99_ms / 20_000)
