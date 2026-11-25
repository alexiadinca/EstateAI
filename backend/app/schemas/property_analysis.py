"""Request and response contracts for property entry and saved analyses."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator, model_validator

from app.extraction.fetcher import UnsupportedListingUrlError, identify_site

# Decimal values are sent to the browser as JSON numbers instead of strings.
JsonDecimal = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]

PropertyType = Literal["apartment", "house"]
BuildingStructure = Literal["concrete", "brick", "aerated_concrete", "wood", "metal", "other"]
PropertyCondition = Literal["new", "renovated", "good", "needs_renovation"]
# The valuation dataset is priced in EUR; other currencies need a conversion policy first.
SupportedCurrency = Literal["EUR"]
AnalysisStatus = Literal["pending", "completed", "unavailable", "failed"]

# How the details reached the form: typed by hand, read from a listing link, or read from
# listing text the user pasted.
InputSource = Literal["manual_entry", "listing_url", "listing_text"]
SupportedListingSite = Literal["storia.ro", "olx.ro"]
# Where a confirmed value came from. Fields missing from the map were entered manually.
FieldOrigin = Literal["listing", "description", "corrected"]
ProvenanceField = Literal[
    "city_id",
    "neighborhood",
    "property_type",
    "usable_area_m2",
    "rooms",
    "floor",
    "total_floors",
    "construction_year",
    "structure",
    "condition",
    "has_balcony",
    "has_elevator",
    "has_parking",
    "asking_price",
]

# Bounds follow the cleaning rules from the ML presentation: values outside them were
# treated as impossible in the listing data (10 to 1,000 m², 1 to 20 rooms).
MIN_USABLE_AREA_M2 = 10
MAX_USABLE_AREA_M2 = 1000
MAX_ROOMS = 20
MIN_FLOOR = -1  # Semi-basement. The ground floor is 0.
MAX_FLOORS = 60
MIN_CONSTRUCTION_YEAR = 1800
# Off-plan apartments can be listed a few years before completion.
FUTURE_CONSTRUCTION_YEARS = 5


class ListingSource(BaseModel):
    """The listing the details were imported from. Coordinates are kept when available."""

    model_config = ConfigDict(extra="forbid")

    site: SupportedListingSite | None = None
    url: str | None = Field(default=None, max_length=2000)
    title: str | None = Field(default=None, max_length=300)
    observed_at: datetime
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class PropertyAnalysisCreate(BaseModel):
    """Property details confirmed by the user on the review step.

    Optional fields left empty are stored as unknown. For lift, balcony and parking,
    null means not stated, while false means the seller stated it is absent.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    city_id: int = Field(gt=0)
    neighborhood: str = Field(min_length=1, max_length=100)
    property_type: PropertyType
    usable_area_m2: Decimal = Field(
        ge=MIN_USABLE_AREA_M2, le=MAX_USABLE_AREA_M2, max_digits=6, decimal_places=2
    )
    rooms: int = Field(ge=1, le=MAX_ROOMS)
    floor: int | None = Field(default=None, ge=MIN_FLOOR, le=MAX_FLOORS)
    total_floors: int | None = Field(default=None, ge=1, le=MAX_FLOORS)
    construction_year: int | None = Field(default=None, ge=MIN_CONSTRUCTION_YEAR)
    structure: BuildingStructure | None = None
    condition: PropertyCondition | None = None
    has_balcony: bool | None = None
    has_elevator: bool | None = None
    has_parking: bool | None = None
    asking_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: SupportedCurrency = "EUR"
    input_source: InputSource = "manual_entry"
    source: ListingSource | None = None
    field_provenance: dict[ProvenanceField, FieldOrigin] = Field(default_factory=dict)

    @field_validator("neighborhood")
    @classmethod
    def collapse_spaces(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("construction_year")
    @classmethod
    def construction_year_not_far_future(cls, value: int | None) -> int | None:
        latest_year = datetime.now(UTC).year + FUTURE_CONSTRUCTION_YEARS
        if value is not None and value > latest_year:
            raise ValueError(f"Construction year cannot be later than {latest_year}.")
        return value

    @model_validator(mode="after")
    def check_floor_rules(self) -> Self:
        if self.property_type == "house" and self.floor is not None:
            raise ValueError("The apartment floor does not apply to a house. Leave it empty.")
        if (
            self.floor is not None
            and self.total_floors is not None
            and self.floor > self.total_floors
        ):
            raise ValueError(
                "The floor cannot be higher than the number of floors in the building."
            )
        return self

    @model_validator(mode="after")
    def check_source_matches_input(self) -> Self:
        if self.input_source == "manual_entry" and (self.source or self.field_provenance):
            raise ValueError("A manually entered property has no listing source.")
        if self.input_source == "listing_url" and (self.source is None or not self.source.url):
            raise ValueError("An imported listing must include its link.")
        if self.input_source == "listing_text" and self.source and self.source.url:
            raise ValueError("Pasted listing text has no link.")
        if self.source and self.source.url:
            try:
                identify_site(self.source.url)
            except UnsupportedListingUrlError as error:
                raise ValueError(str(error)) from error
        return self


class ConfirmedPropertyInputs(BaseModel):
    """Snapshot of the confirmed characteristics, stored with the analysis.

    Reopening an analysis shows these values, even if reference data changes later.
    """

    city: str
    county: str
    neighborhood: str
    property_type: PropertyType
    usable_area_m2: JsonDecimal
    rooms: int
    floor: int | None
    total_floors: int | None
    construction_year: int | None
    structure: BuildingStructure | None
    condition: PropertyCondition | None
    has_balcony: bool | None
    has_elevator: bool | None
    has_parking: bool | None


class ValuationResponse(BaseModel):
    """Result of the valuation step. Estimate fields stay null when no estimate exists."""

    status: AnalysisStatus
    estimated_reference_price: JsonDecimal | None = None
    estimated_price_per_m2: JsonDecimal | None = None
    price_difference_eur: JsonDecimal | None = None
    price_difference_pct: JsonDecimal | None = None
    price_closeness_pct: JsonDecimal | None = None
    model_version: str | None = None
    # Explanation shown when the valuation is unavailable or failed.
    reason: str | None = None


class AnalysisSummary(BaseModel):
    """One row of the "My analyses" list."""

    analysis_id: uuid.UUID
    created_at: datetime
    status: AnalysisStatus
    city: str
    neighborhood: str
    property_type: PropertyType
    rooms: int
    usable_area_m2: JsonDecimal
    asking_price: JsonDecimal
    currency: str


class AnalysisDetail(BaseModel):
    analysis_id: uuid.UUID
    created_at: datetime
    input_source: InputSource
    source: ListingSource | None = None
    field_provenance: dict[ProvenanceField, FieldOrigin] = Field(default_factory=dict)
    property: ConfirmedPropertyInputs
    asking_price: JsonDecimal
    currency: str
    asking_price_per_m2: JsonDecimal
    valuation: ValuationResponse


class CityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    city_id: int
    name: str
    county: str
