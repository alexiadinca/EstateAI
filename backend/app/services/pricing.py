"""Price metrics shared by every screen. Each formula is defined only here.

Amounts are Decimal values in the analysis currency. Results are rounded to two decimals
with ROUND_HALF_UP, the rounding a reader expects from a financial report.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

TWO_DECIMALS = Decimal("0.01")
ONE_HUNDRED = Decimal(100)


def _round(value: Decimal) -> Decimal:
    return value.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


def price_per_m2(price: Decimal, usable_area_m2: Decimal) -> Decimal:
    """Price divided by usable area, for example the asking price per m²."""
    if usable_area_m2 <= 0:
        raise ValueError("Usable area must be positive.")
    return _round(price / usable_area_m2)


@dataclass(frozen=True)
class PriceComparison:
    """How the asking price compares with the estimated reference price."""

    # Positive: the asking price is above the estimate. Negative: below it.
    difference_eur: Decimal
    # Relative to the estimate: 100 × (asking − estimate) / estimate.
    difference_pct: Decimal
    # 100 × smaller price / larger price. Describes two amounts, not model accuracy.
    closeness_pct: Decimal


def compare_asking_price(asking_price: Decimal, estimated_price: Decimal) -> PriceComparison:
    if asking_price <= 0 or estimated_price <= 0:
        raise ValueError("Both prices must be positive.")

    difference = asking_price - estimated_price
    return PriceComparison(
        difference_eur=_round(difference),
        difference_pct=_round(ONE_HUNDRED * difference / estimated_price),
        closeness_pct=_round(
            ONE_HUNDRED * min(asking_price, estimated_price) / max(asking_price, estimated_price)
        ),
    )
