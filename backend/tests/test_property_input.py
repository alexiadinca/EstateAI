import pytest
from pydantic import ValidationError

from app.schemas.property_analysis import PropertyAnalysisCreate

VALID_APARTMENT = {
    "city_id": 2,
    "neighborhood": "  Rogerius  ",
    "property_type": "apartment",
    "usable_area_m2": "54.5",
    "rooms": 2,
    "floor": 3,
    "total_floors": 4,
    "asking_price": "92000",
}


def build(**changes) -> PropertyAnalysisCreate:
    return PropertyAnalysisCreate.model_validate({**VALID_APARTMENT, **changes})


def test_valid_apartment_is_accepted_and_neighborhood_is_tidied():
    request = build()

    assert request.neighborhood == "Rogerius"
    assert request.currency == "EUR"


def test_omitted_amenities_stay_unknown():
    request = build()

    assert request.has_parking is None
    assert request.has_balcony is None


def test_stated_absence_is_kept_as_false():
    assert build(has_parking=False).has_parking is False


def test_house_without_floor_is_accepted():
    request = build(property_type="house", floor=None, total_floors=2)

    assert request.floor is None


@pytest.mark.parametrize(
    "changes",
    [
        {"property_type": "house", "floor": 1},
        {"floor": 5, "total_floors": 4},
        {"usable_area_m2": "0"},
        {"usable_area_m2": "5"},
        {"rooms": 0},
        {"asking_price": "0"},
        {"asking_price": "-1000"},
        {"currency": "RON"},
        {"construction_year": 2200},
        {"neighborhood": "   "},
        {"structure": "cardboard"},
        {"owner_id": "11111111-1111-1111-1111-111111111111"},
    ],
)
def test_invalid_inputs_are_rejected(changes):
    with pytest.raises(ValidationError):
        build(**changes)
