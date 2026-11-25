"""Reference price estimation for a confirmed property.

The regression baseline is trained offline and has not produced a model artifact yet.
Until it exists, every request returns an explicit "unavailable" result with the reason,
so the property is still saved and the user understands why no estimate is shown.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from app.schemas.property_analysis import ConfirmedPropertyInputs

NO_MODEL_AVAILABLE_REASON = (
    "No trained valuation model is available yet. The baseline regression model is still "
    "being prepared, so this property was saved without an estimated reference price."
)


@dataclass(frozen=True)
class ValuationOutcome:
    status: Literal["completed", "unavailable", "failed"]
    estimated_reference_price: Decimal | None = None
    model_version: str | None = None
    reason: str | None = None


def estimate_reference_price(inputs: ConfirmedPropertyInputs) -> ValuationOutcome:
    """Return the model estimate for the inputs, or the reason none can be produced."""
    return ValuationOutcome(status="unavailable", reason=NO_MODEL_AVAILABLE_REASON)
