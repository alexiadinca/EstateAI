"""Values found in a listing, each remembered with where it came from."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal

# "listing": the website's structured data. "description": the seller's free text.
ValueOrigin = Literal["listing", "description"]
TransactionType = Literal["sale", "rent"]


@dataclass
class ListingData:
    """Property details found so far.

    A value that is already known is never replaced, so structured website data, which is
    read first, takes priority over values guessed from the description.
    """

    values: dict[str, Any] = field(default_factory=dict)
    origins: dict[str, ValueOrigin] = field(default_factory=dict)
    city_name: str | None = None
    city_origin: ValueOrigin | None = None
    transaction_type: TransactionType | None = None
    price: Decimal | None = None
    price_currency: str | None = None
    price_origin: ValueOrigin | None = None
    title: str | None = None
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    def add(self, name: str, value: Any, origin: ValueOrigin) -> None:
        if value is None or name in self.values:
            return
        self.values[name] = value
        self.origins[name] = origin

    def add_price(self, amount: Decimal | None, currency: str | None, origin: ValueOrigin) -> None:
        if amount is None or amount <= 0 or self.price is not None:
            return
        self.price = amount
        self.price_currency = currency
        self.price_origin = origin

    def merge_from(self, other: "ListingData") -> None:
        """Fill the gaps in this result with values found elsewhere."""
        for name, value in other.values.items():
            self.add(name, value, other.origins[name])
        self.add_price(other.price, other.price_currency, other.price_origin or "description")
        if not self.city_name and other.city_name:
            self.city_name, self.city_origin = other.city_name, other.city_origin
        self.transaction_type = self.transaction_type or other.transaction_type
