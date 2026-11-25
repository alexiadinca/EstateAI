"""Turning a listing link or pasted listing text into proposed form values.

Order of trust: the website's structured data first, then the seller's description for the
details that are still missing. Every proposed value is checked against the same limits as
the property form; values outside them are dropped with a notice instead of being kept
silently. Nothing is saved here: the user reviews and confirms the values first.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.extraction.fetcher import FetchedPage, fetch_listing_page
from app.extraction.listing_data import ListingData
from app.extraction.olx import parse_olx_page
from app.extraction.storia import parse_storia_page
from app.extraction.text_parser import fold, parse_listing_text
from app.models import City
from app.schemas.extraction import ExtractedValues, ExtractionResponse
from app.schemas.property_analysis import (
    FUTURE_CONSTRUCTION_YEARS,
    MAX_FLOORS,
    MAX_ROOMS,
    MAX_USABLE_AREA_M2,
    MIN_CONSTRUCTION_YEAR,
    MIN_FLOOR,
    MIN_USABLE_AREA_M2,
    ListingSource,
)

PAGE_PARSERS = {"storia": parse_storia_page, "olx": parse_olx_page}

# Names a listing may use for each supported city, compared without diacritics.
CITY_ALIASES = {"bucuresti": "Bucharest", "bucharest": "Bucharest", "craiova": "Craiova"}


def extract_from_url(session: Session, url: str) -> ExtractionResponse:
    page: FetchedPage = fetch_listing_page(url)
    found = PAGE_PARSERS[page.site](page.html)
    # Sellers often put key facts such as rooms or the neighborhood only in the title.
    listing_text = ". ".join(part for part in (found.title, found.description) if part)
    if listing_text:
        found.merge_from(parse_listing_text(listing_text))
    source = ListingSource(
        site=page.domain,
        url=page.url,
        title=found.title,
        observed_at=datetime.now(UTC),
        latitude=found.latitude,
        longitude=found.longitude,
    )
    return _build_response(session, found, "listing_url", source)


def extract_from_text(session: Session, text: str) -> ExtractionResponse:
    found = parse_listing_text(text)
    source = ListingSource(observed_at=datetime.now(UTC))
    return _build_response(session, found, "listing_text", source)


def _build_response(
    session: Session, found: ListingData, input_source: str, source: ListingSource
) -> ExtractionResponse:
    notices: list[str] = []
    values = dict(found.values)
    provenance = dict(found.origins)

    _check_ranges(values, provenance, notices)
    _apply_city(session, found, values, provenance, notices)

    monthly_rent = None
    monthly_rent_currency = None
    if found.transaction_type == "rent":
        monthly_rent, monthly_rent_currency = found.price, found.price_currency
        notices.append(
            "This is a rental listing. Its details were filled in, but the rent is not an "
            "asking price: EstateAI compares sale prices. Enter a sale price to continue."
        )
    elif found.price is not None and found.price_currency == "EUR":
        values["asking_price"] = found.price
        provenance["asking_price"] = found.price_origin or "listing"
    elif found.price is not None:
        notices.append(
            f"The listing price is in {found.price_currency}. EstateAI analyzes prices in "
            "euro, so enter the asking price in EUR."
        )

    if not values:
        notices.append("No property details were recognised. Fill in the form manually.")

    return ExtractionResponse(
        input_source=input_source,
        source=source,
        transaction_type=found.transaction_type,
        monthly_rent=monthly_rent,
        monthly_rent_currency=monthly_rent_currency,
        values=ExtractedValues(**values),
        provenance=provenance,
        notices=notices,
    )


def _apply_city(
    session: Session,
    found: ListingData,
    values: dict[str, Any],
    provenance: dict[str, str],
    notices: list[str],
) -> None:
    if not found.city_name:
        return
    supported_name = CITY_ALIASES.get(fold(found.city_name).strip())
    city = (
        session.scalars(select(City).where(City.name == supported_name)).first()
        if supported_name
        else None
    )
    if city is None:
        notices.append(
            f"This property is in {found.city_name}. Valuations currently cover only "
            "Bucharest and Craiova."
        )
        values.pop("neighborhood", None)
        provenance.pop("neighborhood", None)
        return
    values["city_id"] = city.city_id
    provenance["city_id"] = found.city_origin or "description"


def _check_ranges(values: dict[str, Any], provenance: dict[str, str], notices: list[str]) -> None:
    latest_year = datetime.now(UTC).year + FUTURE_CONSTRUCTION_YEARS
    limits = {
        "usable_area_m2": (Decimal(MIN_USABLE_AREA_M2), Decimal(MAX_USABLE_AREA_M2), "usable area"),
        "rooms": (1, MAX_ROOMS, "number of rooms"),
        "floor": (MIN_FLOOR, MAX_FLOORS, "floor"),
        "total_floors": (1, MAX_FLOORS, "number of floors"),
        "construction_year": (MIN_CONSTRUCTION_YEAR, latest_year, "construction year"),
    }
    for name, (lowest, highest, label) in limits.items():
        value = values.get(name)
        if value is not None and not lowest <= value <= highest:
            _drop(values, provenance, name)
            notices.append(f"The listing's {label} ({value}) is outside the supported range.")

    floor, total_floors = values.get("floor"), values.get("total_floors")
    if floor is not None and total_floors is not None and floor > total_floors:
        _drop(values, provenance, "floor")
        _drop(values, provenance, "total_floors")
        notices.append("The floor and the number of floors in the listing contradict each other.")


def _drop(values: dict[str, Any], provenance: dict[str, str], name: str) -> None:
    values.pop(name, None)
    provenance.pop(name, None)
