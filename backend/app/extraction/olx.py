"""Reading an olx.ro listing page.

OLX pages embed the listing as a JSON string in window.__PRERENDERED_STATE__. OLX provides
few structured fields for real estate, so most details come from the seller's description.
"""

import json
import re
from decimal import Decimal
from typing import Any

from app.extraction.fetcher import ListingUnavailableError
from app.extraction.listing_data import ListingData
from app.extraction.text_parser import fold

ORIGIN = "listing"

_STATE_MARKER = "window.__PRERENDERED_STATE__"
_JSON_STRING = re.compile(r'\s*=\s*("(?:[^"\\]|\\.)*")')


def parse_olx_page(html: str) -> ListingData:
    state = _read_state(html)
    ad = state["ad"]["ad"]
    found = ListingData(title=ad.get("title"))

    # The breadcrumb names the category, for example "Apartamente - Garsoniere de inchiriat".
    category = " ".join(fold(b.get("label") or "") for b in state["ad"].get("breadcrumbs") or [])
    if "apartament" in category or "garsonier" in category:
        found.add("property_type", "apartment", ORIGIN)
    elif "case" in category:
        found.add("property_type", "house", ORIGIN)
    if "de inchiriat" in category:
        found.transaction_type = "rent"
    elif "de vanzare" in category:
        found.transaction_type = "sale"

    for parameter in ad.get("params") or []:
        _read_parameter(parameter, found)

    _read_price(ad.get("price") or {}, found)
    location = ad.get("location") or {}
    found.city_name = location.get("cityName")
    found.city_origin = ORIGIN if found.city_name else None
    found.add("neighborhood", location.get("districtName"), ORIGIN)
    coordinates = ad.get("map") or {}
    found.latitude = coordinates.get("lat")
    found.longitude = coordinates.get("lon")
    found.description = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", ad.get("description") or ""))
    return found


def _read_state(html: str) -> dict[str, Any]:
    start = html.find(_STATE_MARKER)
    match = _JSON_STRING.match(html, start + len(_STATE_MARKER)) if start >= 0 else None
    try:
        state = json.loads(json.loads(match.group(1))) if match else None
        if state and state["ad"]["ad"]:
            return state
    except (ValueError, KeyError, TypeError):
        pass
    raise ListingUnavailableError(
        "The listing details could not be read from this olx.ro page. "
        "It may have expired. Paste the listing text instead."
    )


def _read_parameter(parameter: dict[str, Any], found: ListingData) -> None:
    key = parameter.get("key")
    normalized = str(parameter.get("normalizedValue") or "")
    if key == "m" and re.fullmatch(r"\d+(?:\.\d+)?", normalized):
        found.add("usable_area_m2", Decimal(normalized), ORIGIN)
    elif key == "floor":
        found.add("floor", _floor(normalized), ORIGIN)
    elif key == "rooms":
        # "four" means "4 or more", which is not an exact count.
        exact = {"one": 1, "two": 2, "three": 3}.get(normalized)
        found.add("rooms", exact, ORIGIN)
    elif key == "constructie" and re.fullmatch(r"(?:18|19|20)\d\d", normalized):
        # Ranges such as "1977-1990" or "dupa-2000" are not an exact year and are skipped.
        found.add("construction_year", int(normalized), ORIGIN)


def _floor(normalized: str) -> int | None:
    if normalized in ("parter", "fl_0"):
        return 0
    if normalized == "demisol":
        return -1
    if match := re.fullmatch(r"fl_(\d{1,2})", normalized):
        return int(match.group(1))
    return None


def _read_price(price: dict[str, Any], found: ListingData) -> None:
    """Uses the price as the seller displayed it, for example "123 000 €" or "450 000 lei"."""
    display = fold(price.get("displayValue") or "")
    match = re.search(r"(\d[\d ]*)\s*(€|eur|lei|ron)", display)
    if match:
        amount = Decimal(match.group(1).replace(" ", ""))
        currency = "EUR" if match.group(2) in ("€", "eur") else "RON"
        found.add_price(amount, currency, ORIGIN)
