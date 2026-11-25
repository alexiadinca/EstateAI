"""Reading property details from Romanian listing text."""

from decimal import Decimal

from app.extraction.text_parser import parse_listing_text

APARTMENT_TEXT = """
Vand apartament 2 camere decomandat in Craiova, zona Rogerius.
Suprafata utila 54 mp, etaj 3/4, bloc din 1985, structura din beton armat.
Apartamentul este renovat complet, are balcon inchis, fara lift.
Loc de parcare in fata blocului. Pret: 92.000 euro, negociabil.
"""


def test_apartment_description_is_read():
    found = parse_listing_text(APARTMENT_TEXT)

    assert found.values == {
        "property_type": "apartment",
        "neighborhood": "Rogerius",
        "rooms": 2,
        "usable_area_m2": Decimal("54"),
        "construction_year": 1985,
        "structure": "concrete",
        "condition": "renovated",
        "has_balcony": True,
        "has_parking": True,
        "floor": 3,
        "total_floors": 4,
        "has_elevator": False,
    }
    assert found.city_name == "Craiova"
    assert found.transaction_type == "sale"
    assert found.price == Decimal("92000")
    assert found.price_currency == "EUR"
    assert set(found.origins.values()) == {"description"}


def test_diacritics_and_spelled_numbers_are_understood():
    found = parse_listing_text("Apartament cu două camere în București, sectorul 3, 48,5 mp utili.")

    assert found.values["rooms"] == 2
    assert found.values["usable_area_m2"] == Decimal("48.5")
    assert found.city_name == "Bucharest"


def test_details_that_are_not_mentioned_stay_unknown():
    found = parse_listing_text("Apartament luminos, aproape de parc si scoli, in Craiova.")

    for name in ("rooms", "usable_area_m2", "floor", "has_parking", "has_elevator"):
        assert name not in found.values


def test_land_and_built_areas_are_not_taken_as_usable_area():
    found = parse_listing_text("Casa de vanzare, teren 347 mp, suprafata construita 106 mp.")

    assert "usable_area_m2" not in found.values


def test_house_levels_are_not_read_as_an_apartment_floor():
    found = parse_listing_text(
        "Vand casa in Craiova. Parter: living si bucatarie. Etaj 1: 3 dormitoare."
    )

    assert found.values["property_type"] == "house"
    assert "floor" not in found.values
    assert "has_elevator" not in found.values


def test_apartment_in_a_duplex_house_is_an_apartment():
    found = parse_listing_text("Apartament in casa tip duplex, intrare separata.")

    assert found.values["property_type"] == "apartment"


def test_ground_floor_and_building_height():
    found = parse_listing_text("Garsoniera situata la parter, bloc P+4, cu lift.")

    assert found.values["floor"] == 0
    assert found.values["total_floors"] == 4
    assert found.values["rooms"] == 1
    assert found.values["has_elevator"] is True


def test_rental_listing_is_recognised():
    found = parse_listing_text("Inchiriez apartament 3 camere, chirie 500 euro/luna.")

    assert found.transaction_type == "rent"
    assert found.price == Decimal("500")


def test_price_in_lei_keeps_its_currency():
    found = parse_listing_text("Apartament 2 camere, pret 450 000 lei.")

    assert found.price == Decimal("450000")
    assert found.price_currency == "RON"


def test_needs_renovation_is_not_mistaken_for_renovated():
    found = parse_listing_text("Apartament 2 camere care necesita renovare.")

    assert found.values["condition"] == "needs_renovation"
