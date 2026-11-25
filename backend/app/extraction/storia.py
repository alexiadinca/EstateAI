"""Reading a storia.ro listing page.

Storia pages embed the listing as JSON in the __NEXT_DATA__ script. The values used here
are the ones observed on real sale and rent pages for apartments and houses.
"""

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from app.extraction.fetcher import ListingUnavailableError
from app.extraction.listing_data import ListingData

ORIGIN = "listing"

_NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)

PROPERTY_TYPES = {"FLAT": "apartment", "HOUSE": "house"}
TRANSACTION_TYPES = {"SELL": "sale", "RENT": "rent"}
MATERIALS = {
    "brick": "brick",
    "concrete": "concrete",
    "reinforced_concrete": "concrete",
    "concrete_plate": "concrete",
    "cellular_concrete": "aerated_concrete",
    "breezeblock": "aerated_concrete",
    "wood": "wood",
    "metal": "metal",
    "other": "other",
}
CITY_LEVELS = {"city", "county_capital"}
NEIGHBORHOOD_LEVELS = {"district", "residential"}


def parse_storia_page(html: str) -> ListingData:
    ad = _read_ad(html)
    found = ListingData(title=ad.get("title"))
    target = ad.get("target") or {}
    category = ad.get("adCategory") or {}

    property_type = PROPERTY_TYPES.get(category.get("name"))
    found.add("property_type", property_type, ORIGIN)
    found.transaction_type = TRANSACTION_TYPES.get(category.get("type"))

    found.add("usable_area_m2", _decimal(target.get("Area")), ORIGIN)
    found.add("rooms", _first_int(target.get("Rooms_num")), ORIGIN)
    found.add("construction_year", _int(target.get("Build_year")), ORIGIN)
    found.add("structure", MATERIALS.get(_first(target.get("Building_material"))), ORIGIN)
    found.add("condition", _condition(target), ORIGIN)

    extras = set(target.get("Extras_types") or [])
    # Storia lists amenities that are present. A missing entry means "not stated", not "no".
    found.add("has_balcony", True if "balcony" in extras else None, ORIGIN)
    found.add("has_parking", True if extras & {"garage", "parking"} else None, ORIGIN)

    if property_type == "apartment":
        found.add("floor", _floor(_first(target.get("Floor_no"))), ORIGIN)
        found.add("total_floors", _int(target.get("Building_floors_num")), ORIGIN)
        found.add("has_elevator", _lift(ad, extras), ORIGIN)

    _read_price(ad, found)
    _read_location(ad, found)
    found.description = _plain_text(ad.get("description"))
    return found


def _read_ad(html: str) -> dict[str, Any]:
    match = _NEXT_DATA.search(html)
    try:
        ad = json.loads(match.group(1))["props"]["pageProps"]["ad"] if match else None
    except (ValueError, KeyError, TypeError):
        ad = None
    if not ad:
        raise ListingUnavailableError(
            "The listing details could not be read from this storia.ro page. "
            "It may have expired. Paste the listing text instead."
        )
    return ad


def _read_price(ad: dict[str, Any], found: ListingData) -> None:
    for item in ad.get("characteristics") or []:
        if item.get("key") == "price":
            found.add_price(_decimal(item.get("value")), item.get("currency") or None, ORIGIN)
            return


def _read_location(ad: dict[str, Any], found: ListingData) -> None:
    location = ad.get("location") or {}
    for place in (location.get("reverseGeocoding") or {}).get("locations") or []:
        level = place.get("locationLevel")
        if level in CITY_LEVELS:
            found.city_name = place.get("name")
            found.city_origin = ORIGIN
        elif level in NEIGHBORHOOD_LEVELS:
            found.add("neighborhood", place.get("name"), ORIGIN)
    coordinates = location.get("coordinates") or {}
    found.latitude = coordinates.get("latitude")
    found.longitude = coordinates.get("longitude")


def _condition(target: dict[str, Any]) -> str | None:
    if "to_renovation" in (target.get("Construction_status") or []):
        return "needs_renovation"
    # The primary market on storia means a newly built property sold by the developer.
    if target.get("MarketType") == "primary":
        return "new"
    return None


def _lift(ad: dict[str, Any], extras: set[str]) -> bool | None:
    for item in ad.get("additionalInformation") or []:
        if item.get("label") == "lift":
            values = item.get("values") or []
            if values == ["::y"]:
                return True
            if values == ["::n"]:
                return False
    return True if "lift" in extras else None


def _floor(value: str | None) -> int | None:
    """Storia floor codes: "floor_6", "ground_floor", "cellar"; higher floors are ranges."""
    if value == "ground_floor":
        return 0
    if value == "cellar":
        return -1
    if value and (match := re.fullmatch(r"floor_(\d{1,2})", value)):
        return int(match.group(1))
    return None


def _plain_text(html_text: str | None) -> str | None:
    if not html_text:
        return None
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_text)).strip()


def _first(values: Any) -> Any:
    return values[0] if isinstance(values, list) and values else None


def _first_int(values: Any) -> int | None:
    return _int(_first(values))


def _int(value: Any) -> int | None:
    return int(value) if isinstance(value, (int, str)) and str(value).isdigit() else None


def _decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value)) if value not in (None, "") else None
    except InvalidOperation:
        return None
