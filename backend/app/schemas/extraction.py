"""Request and response contracts for importing details from a listing."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.property_analysis import (
    BuildingStructure,
    InputSource,
    JsonDecimal,
    ListingSource,
    PropertyCondition,
    PropertyType,
)

MAX_PASTED_TEXT_LENGTH = 20_000
MIN_PASTED_TEXT_LENGTH = 30


class ExtractionRequest(BaseModel):
    """Either the link of a listing page or the text of a listing, not both."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    url: str | None = Field(default=None, max_length=2000)
    text: str | None = Field(
        default=None, min_length=MIN_PASTED_TEXT_LENGTH, max_length=MAX_PASTED_TEXT_LENGTH
    )

    @model_validator(mode="after")
    def exactly_one_input(self) -> Self:
        if bool(self.url) == bool(self.text):
            raise ValueError("Provide either a listing link or the listing text.")
        return self


class ExtractedValues(BaseModel):
    """Proposed form values. Every field may be null when the listing does not state it."""

    city_id: int | None = None
    neighborhood: str | None = None
    property_type: PropertyType | None = None
    usable_area_m2: JsonDecimal | None = None
    rooms: int | None = None
    floor: int | None = None
    total_floors: int | None = None
    construction_year: int | None = None
    structure: BuildingStructure | None = None
    condition: PropertyCondition | None = None
    has_balcony: bool | None = None
    has_elevator: bool | None = None
    has_parking: bool | None = None
    asking_price: JsonDecimal | None = None


class ExtractionResponse(BaseModel):
    input_source: InputSource
    source: ListingSource
    transaction_type: Literal["sale", "rent"] | None
    # Rent stated in a rental listing; it is never used as the asking price.
    monthly_rent: JsonDecimal | None = None
    monthly_rent_currency: str | None = None
    values: ExtractedValues
    # Origin of each proposed value: the website's structured data or the description.
    provenance: dict[str, Literal["listing", "description"]]
    # Messages the user should read before reviewing, for example about unsupported values.
    notices: list[str]
