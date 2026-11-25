"""Reading storia.ro and olx.ro pages.

The pages below are small synthetic examples that follow the structure observed on real
listing pages in November 2026, so the tests run without network access.
"""

import json
from decimal import Decimal

import pytest

from app.extraction.fetcher import ListingUnavailableError
from app.extraction.olx import parse_olx_page
from app.extraction.storia import parse_storia_page


def storia_page(ad: dict) -> str:
    data = json.dumps({"props": {"pageProps": {"ad": ad}}})
    script = '<script id="__NEXT_DATA__" type="application/json" crossorigin="anonymous">'
    return f"<html>{script}{data}</script></html>"


STORIA_APARTMENT = {
    "title": "Apartament 3 camere, George Enescu",
    "adCategory": {"id": 101, "name": "FLAT", "type": "SELL"},
    "target": {
        "Area": "118",
        "Rooms_num": ["3"],
        "Floor_no": ["floor_1"],
        "Building_floors_num": "2",
        "Build_year": "2014",
        "Building_material": ["brick"],
        "Extras_types": ["balcony", "garage", "terrace"],
        "MarketType": "secondary",
        "Construction_status": ["ready_to_use"],
    },
    "characteristics": [{"key": "price", "value": "370000", "currency": "EUR"}],
    "additionalInformation": [{"label": "lift", "values": ["::n"], "unit": ""}],
    "location": {
        "coordinates": {"latitude": 44.32, "longitude": 23.79},
        "reverseGeocoding": {
            "locations": [
                {"locationLevel": "county", "name": "Dolj"},
                {"locationLevel": "county_capital", "name": "Craiova"},
                {"locationLevel": "district", "name": "George Enescu"},
            ]
        },
    },
    "description": "<p>Apartament <b>spatios</b>.</p>",
}


def test_storia_apartment_is_read_from_its_structured_data():
    found = parse_storia_page(storia_page(STORIA_APARTMENT))

    assert found.values == {
        "property_type": "apartment",
        "usable_area_m2": Decimal("118"),
        "rooms": 3,
        "construction_year": 2014,
        "structure": "brick",
        "has_balcony": True,
        "has_parking": True,
        "floor": 1,
        "total_floors": 2,
        "has_elevator": False,
        "neighborhood": "George Enescu",
    }
    assert set(found.origins.values()) == {"listing"}
    assert found.city_name == "Craiova"
    assert found.transaction_type == "sale"
    assert (found.price, found.price_currency) == (Decimal("370000"), "EUR")
    assert (found.latitude, found.longitude) == (44.32, 23.79)
    assert found.description == "Apartament spatios ."


def test_storia_house_has_no_apartment_floor_or_lift():
    house = {
        **STORIA_APARTMENT,
        "adCategory": {"id": 201, "name": "HOUSE", "type": "SELL"},
        "target": {"Area": "80", "Rooms_num": ["3"], "Floor_no": ["floor_1"]},
    }

    found = parse_storia_page(storia_page(house))

    assert found.values["property_type"] == "house"
    assert "floor" not in found.values
    assert "has_elevator" not in found.values


def test_storia_amenities_not_listed_stay_unknown():
    found = parse_storia_page(storia_page({**STORIA_APARTMENT, "target": {"Area": "50"}}))

    assert "has_balcony" not in found.values
    assert "has_parking" not in found.values


def test_storia_rental_and_primary_market():
    rental = {
        **STORIA_APARTMENT,
        "adCategory": {"id": 102, "name": "FLAT", "type": "RENT"},
        "target": {"Area": "60", "MarketType": "primary"},
    }

    found = parse_storia_page(storia_page(rental))

    assert found.transaction_type == "rent"
    assert found.values["condition"] == "new"


def test_storia_page_without_listing_data_is_reported():
    with pytest.raises(ListingUnavailableError):
        parse_storia_page("<html><body>Anunt expirat</body></html>")


def olx_page(ad: dict, breadcrumbs: list[str]) -> str:
    state = {"ad": {"ad": ad, "breadcrumbs": [{"label": label} for label in breadcrumbs]}}
    # OLX stores the state as a JSON string inside a script, so it is encoded twice.
    return f"<script>window.__PRERENDERED_STATE__= {json.dumps(json.dumps(state))};</script>"


OLX_APARTMENT = {
    "title": "Apartament 3 camere, zona Ford Capsunarie",
    "price": {"displayValue": "123 000 €"},
    "params": [
        {"key": "m", "normalizedValue": "51"},
        {"key": "floor", "normalizedValue": "fl_3"},
        {"key": "constructie", "normalizedValue": "1977-1990"},
    ],
    "location": {"cityName": "Craiova", "districtName": None},
    "map": {"lat": 44.32, "lon": 23.81},
    "description": "Apartament cu parcare.",
}


def test_olx_apartment_is_read():
    found = parse_olx_page(
        olx_page(OLX_APARTMENT, ["Imobiliare", "Apartamente - Garsoniere de vanzare"])
    )

    assert found.values == {
        "property_type": "apartment",
        "usable_area_m2": Decimal("51"),
        "floor": 3,
    }
    assert found.transaction_type == "sale"
    assert (found.price, found.price_currency) == (Decimal("123000"), "EUR")
    assert found.city_name == "Craiova"
    assert found.title == "Apartament 3 camere, zona Ford Capsunarie"


def test_olx_year_range_is_not_used_as_an_exact_year():
    found = parse_olx_page(olx_page(OLX_APARTMENT, ["Apartamente - Garsoniere de vanzare"]))

    assert "construction_year" not in found.values


def test_olx_rental_house_with_price_in_lei():
    rental = {**OLX_APARTMENT, "price": {"displayValue": "2 500 lei"}, "params": []}

    found = parse_olx_page(olx_page(rental, ["Case de inchiriat"]))

    assert found.values["property_type"] == "house"
    assert found.transaction_type == "rent"
    assert found.price_currency == "RON"


def test_olx_page_without_listing_data_is_reported():
    with pytest.raises(ListingUnavailableError):
        parse_olx_page("<html>Anuntul nu mai este disponibil</html>")
