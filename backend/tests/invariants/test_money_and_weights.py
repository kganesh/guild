"""Money and weight invariants.

These are the tests that stand in for a compiler. See ADR 0006.
"""

from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from guild.shared.money import Money, Price, Quantity
from guild.shared.weight import BASIS_POINTS_TOTAL, Weight, assert_totals_to_one


class TestFloatsAreRejected:
    def test_money_rejects_float(self):
        with pytest.raises(TypeError):
            Money(513.99)

    def test_price_rejects_float(self):
        with pytest.raises(TypeError):
            Price(62.594)

    def test_quantity_rejects_float(self):
        with pytest.raises(TypeError):
            Quantity(8.2114)

    def test_weight_rejects_float(self):
        with pytest.raises(TypeError):
            Weight(2850.0)

    def test_weight_from_percent_rejects_float(self):
        with pytest.raises(TypeError):
            Weight.from_percent(28.5)


class TestMoneyArithmetic:
    def test_addition_is_exact(self):
        total = Money("0.1") + Money("0.2")
        assert total.amount == Decimal("0.3")

    def test_currency_mismatch_raises(self):
        with pytest.raises(ValueError):
            Money("1", "USD") + Money("1", "EUR")

    def test_price_times_quantity(self):
        value = Price("62.5940").times(Quantity("8.2114"))
        assert value.amount == Decimal("62.5940") * Decimal("8.2114")


class TestWeights:
    def test_from_percent(self):
        assert Weight.from_percent("28.5").basis_points == 2850

    def test_sub_basis_point_precision_is_rejected(self):
        with pytest.raises(ValueError):
            Weight.from_percent("28.505")

    def test_strategy_must_total_exactly(self):
        strategy = [
            Weight.from_percent("40"),
            Weight.from_percent("28"),
            Weight.from_percent("19"),
            Weight.from_percent("13"),
        ]
        assert_totals_to_one(strategy)

    def test_near_miss_is_rejected(self):
        with pytest.raises(ValueError):
            assert_totals_to_one([Weight.from_percent("99.99")])

    @given(st.lists(st.integers(min_value=0, max_value=BASIS_POINTS_TOTAL), min_size=1))
    def test_only_exact_totals_pass(self, points):
        weights = [Weight(p) for p in points]
        if sum(points) == BASIS_POINTS_TOTAL:
            assert_totals_to_one(weights)
        else:
            with pytest.raises(ValueError):
                assert_totals_to_one(weights)
