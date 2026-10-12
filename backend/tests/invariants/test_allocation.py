"""Allocation invariants — the product's central fairness claim, as tests.

1. Every account in a batch is booked at the same average price.
2. Allocated quantities sum exactly to what was filled; the remainder sits with the firm.

See ADR 0003.
"""

from decimal import Decimal

import pytest
from hypothesis import given, settings, strategies as st

from guild.domain.trading.allocation import (
    AllocationLine,
    AllocationStatement,
    Fill,
    allocate,
    average_price,
)
from guild.shared.money import Price, Quantity


def statement(*quantities: str) -> AllocationStatement:
    return AllocationStatement(
        batch_id="batch-1",
        instrument="SEMI",
        lines=[
            AllocationLine(f"acct-{i}", Quantity(q)) for i, q in enumerate(quantities)
        ],
    )


class TestAveragePrice:
    def test_volume_weighted(self):
        fills = [
            Fill(Quantity("1000"), Price("62.50")),
            Fill(Quantity("3000"), Price("62.60")),
        ]
        # (1000*62.50 + 3000*62.60) / 4000
        assert average_price(fills).value == Decimal("62.5750")

    def test_no_fills_raises(self):
        with pytest.raises(ValueError):
            average_price([])


class TestFullFill:
    def test_everyone_gets_their_stated_quantity(self):
        result = allocate(statement("10", "20", "70"), [Fill(Quantity("100"), Price("10"))])
        assert result.per_account["acct-0"].shares == Decimal("10.000000")
        assert result.per_account["acct-2"].shares == Decimal("70.000000")
        assert result.firm_residual.is_zero()

    def test_one_price_for_everyone(self):
        fills = [
            Fill(Quantity("40"), Price("10.00")),
            Fill(Quantity("60"), Price("10.50")),
        ]
        result = allocate(statement("50", "50"), fills)
        # A single price object is applied to the whole batch; there is no per-account price.
        assert result.price.value == Decimal("10.3000")


class TestPartialFill:
    def test_scaled_pro_rata(self):
        result = allocate(statement("25", "75"), [Fill(Quantity("40"), Price("10"))])
        assert result.per_account["acct-0"].shares == Decimal("10.000000")
        assert result.per_account["acct-1"].shares == Decimal("30.000000")

    def test_overfill_is_rejected(self):
        with pytest.raises(ValueError):
            allocate(statement("10"), [Fill(Quantity("11"), Price("10"))])


class TestConservation:
    @settings(max_examples=200)
    @given(
        quantities=st.lists(
            st.integers(min_value=1, max_value=10_000), min_size=1, max_size=50
        ),
        fill_pct=st.integers(min_value=1, max_value=100),
    )
    def test_allocations_never_exceed_the_fill(self, quantities, fill_pct):
        stmt = statement(*[str(q) for q in quantities])
        filled = (stmt.total.shares * Decimal(fill_pct) / 100).quantize(Decimal("0.000001"))
        if filled <= 0:
            return

        result = allocate(stmt, [Fill(Quantity(filled), Price("10"))])
        allocated = sum(
            (q.shares for q in result.per_account.values()), Decimal("0")
        )

        # Nothing is created out of rounding, and nothing vanishes: the residual is
        # explicit and belongs to the firm, never to whichever member rounds last.
        assert allocated + result.firm_residual.shares == filled
        assert result.firm_residual.shares >= 0
