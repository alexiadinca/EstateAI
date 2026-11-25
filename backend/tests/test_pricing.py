from decimal import Decimal

import pytest

from app.services.pricing import compare_asking_price, price_per_m2


def test_valuation_acceptance_example_from_requirements():
    # Asking price €100,000 and estimate €88,000: +€12,000, 13.64% above, 88% closeness.
    comparison = compare_asking_price(Decimal("100000"), Decimal("88000"))

    assert comparison.difference_eur == Decimal("12000.00")
    assert comparison.difference_pct == Decimal("13.64")
    assert comparison.closeness_pct == Decimal("88.00")


def test_investment_example_asking_price_above_estimate():
    comparison = compare_asking_price(Decimal("125000"), Decimal("117400"))

    assert comparison.difference_pct == Decimal("6.47")


def test_asking_price_below_estimate_gives_negative_difference():
    comparison = compare_asking_price(Decimal("80000"), Decimal("88000"))

    assert comparison.difference_eur == Decimal("-8000.00")
    assert comparison.difference_pct == Decimal("-9.09")
    assert comparison.closeness_pct == Decimal("90.91")


def test_equal_prices():
    comparison = compare_asking_price(Decimal("88000"), Decimal("88000"))

    assert comparison.difference_eur == Decimal("0.00")
    assert comparison.difference_pct == Decimal("0.00")
    assert comparison.closeness_pct == Decimal("100.00")


def test_changing_only_the_asking_price_keeps_the_estimate_as_the_denominator():
    lower = compare_asking_price(Decimal("90000"), Decimal("88000"))
    higher = compare_asking_price(Decimal("110000"), Decimal("88000"))

    assert lower.difference_eur == Decimal("2000.00")
    assert higher.difference_eur == Decimal("22000.00")


@pytest.mark.parametrize(
    "asking, estimate", [(Decimal("0"), Decimal("1")), (Decimal("1"), Decimal("0"))]
)
def test_non_positive_prices_are_rejected(asking, estimate):
    with pytest.raises(ValueError):
        compare_asking_price(asking, estimate)


def test_price_per_m2_is_rounded_to_cents():
    assert price_per_m2(Decimal("92000"), Decimal("54")) == Decimal("1703.70")


def test_price_per_m2_rejects_zero_area():
    with pytest.raises(ValueError):
        price_per_m2(Decimal("92000"), Decimal("0"))
