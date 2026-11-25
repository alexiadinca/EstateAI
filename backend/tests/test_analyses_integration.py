"""Integration tests for saving and reopening analyses against the real database.

Each test runs inside a transaction that is rolled back afterwards, so no data remains.
The tests use the two Supabase test accounts and are skipped when the database or the
accounts are not available.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.token_verifier import AuthenticatedUser
from app.core.config import get_settings
from app.db.session import get_db_session, get_engine
from app.main import app

TEST_ACCOUNT_EMAILS = ("demo1@estateai.test", "demo2@estateai.test")

pytestmark = pytest.mark.skipif(
    get_settings().database_url is None, reason="DATABASE_URL is not configured."
)


@pytest.fixture
def db_session() -> Iterator[Session]:
    connection = get_engine().connect()
    outer_transaction = connection.begin()
    # Commits inside the application only release a savepoint; the outer rollback undoes all.
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture
def test_users(db_session) -> tuple[AuthenticatedUser, AuthenticatedUser]:
    query = text("select id, email from auth.users where email in :emails").bindparams(
        bindparam("emails", expanding=True)
    )
    rows = db_session.execute(query, {"emails": list(TEST_ACCOUNT_EMAILS)}).all()
    users = {row.email: AuthenticatedUser(row.id, row.email, None, None) for row in rows}
    if len(users) < 2:
        pytest.skip("The two Supabase test accounts do not exist.")
    return users[TEST_ACCOUNT_EMAILS[0]], users[TEST_ACCOUNT_EMAILS[1]]


@pytest.fixture
def api(db_session):
    """Client whose requests use the test transaction and a chosen signed-in user."""
    signed_in = {}
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: signed_in["user"]

    def as_user(user: AuthenticatedUser) -> TestClient:
        signed_in["user"] = user
        return TestClient(app)

    yield as_user
    app.dependency_overrides.clear()


def craiova_id(db_session) -> int:
    return db_session.execute(text("select city_id from city where name = 'Craiova'")).scalar_one()


def apartment_payload(city_id: int, **changes) -> dict:
    return {
        "city_id": city_id,
        "neighborhood": "Rogerius",
        "property_type": "apartment",
        "usable_area_m2": 54,
        "rooms": 2,
        "floor": 3,
        "total_floors": 4,
        "has_balcony": False,
        "asking_price": 92000,
        "currency": "EUR",
        **changes,
    }


def test_owner_saves_and_reopens_the_original_snapshot(api, test_users, db_session):
    owner, _ = test_users
    client = api(owner)

    created = client.post("/analyses", json=apartment_payload(craiova_id(db_session)))
    assert created.status_code == 201
    analysis = created.json()
    assert analysis["valuation"]["status"] == "unavailable"
    assert analysis["valuation"]["reason"]
    assert analysis["valuation"]["estimated_reference_price"] is None
    assert analysis["asking_price_per_m2"] == 1703.70

    reopened = client.get(f"/analyses/{analysis['analysis_id']}")
    assert reopened.status_code == 200
    assert reopened.json() == analysis
    assert reopened.json()["property"]["has_parking"] is None
    assert reopened.json()["property"]["has_balcony"] is False

    listed = client.get("/analyses").json()
    assert analysis["analysis_id"] in [item["analysis_id"] for item in listed]


def test_another_user_cannot_read_or_list_the_analysis(api, test_users, db_session):
    owner, other_user = test_users
    created = api(owner).post("/analyses", json=apartment_payload(craiova_id(db_session)))
    analysis_id = created.json()["analysis_id"]

    other_client = api(other_user)
    assert other_client.get(f"/analyses/{analysis_id}").status_code == 404
    assert analysis_id not in [item["analysis_id"] for item in other_client.get("/analyses").json()]


def test_house_is_saved_with_floor_not_applicable(api, test_users, db_session):
    owner, _ = test_users
    payload = apartment_payload(
        craiova_id(db_session), property_type="house", floor=None, total_floors=2, rooms=4
    )

    response = api(owner).post("/analyses", json=payload)

    assert response.status_code == 201
    assert response.json()["property"]["floor"] is None


def test_unsupported_city_is_rejected(api, test_users):
    owner, _ = test_users

    response = api(owner).post("/analyses", json=apartment_payload(999999))

    assert response.status_code == 422


def test_pasted_listing_text_proposes_values_without_saving(api, test_users, db_session):
    owner, _ = test_users
    text = (
        "Vand apartament 2 camere in Craiova, zona Rogerius, 54 mp utili, etaj 3/4. "
        "Pret 92.000 euro."
    )

    response = api(owner).post("/extractions", json={"text": text})

    assert response.status_code == 200
    body = response.json()
    assert body["input_source"] == "listing_text"
    assert body["values"]["city_id"] == craiova_id(db_session)
    assert body["values"]["rooms"] == 2
    assert body["values"]["asking_price"] == 92000
    assert body["provenance"]["rooms"] == "description"
    assert api(owner).get("/analyses").json() == []


def test_unsupported_listing_link_is_rejected_with_an_explanation(api, test_users):
    owner, _ = test_users

    response = api(owner).post(
        "/extractions", json={"url": "https://www.imobiliare.ro/oferta/apartament-123"}
    )

    assert response.status_code == 422
    assert "paste the listing text" in response.json()["detail"]


def test_imported_listing_keeps_its_source_and_field_origins(api, test_users, db_session):
    owner, _ = test_users
    payload = apartment_payload(
        craiova_id(db_session),
        input_source="listing_url",
        source={
            "site": "storia.ro",
            "url": "https://www.storia.ro/ro/oferta/apartament-IDabc",
            "title": "Apartament 2 camere",
            "observed_at": "2026-11-25T10:00:00Z",
            "latitude": 44.32,
            "longitude": 23.79,
        },
        field_provenance={"rooms": "listing", "floor": "description", "asking_price": "corrected"},
    )

    created = api(owner).post("/analyses", json=payload)
    assert created.status_code == 201
    reopened = api(owner).get(f"/analyses/{created.json()['analysis_id']}").json()

    assert reopened["input_source"] == "listing_url"
    assert reopened["source"]["url"] == "https://www.storia.ro/ro/oferta/apartament-IDabc"
    assert reopened["field_provenance"] == {
        "rooms": "listing",
        "floor": "description",
        "asking_price": "corrected",
    }


def test_saved_source_link_must_come_from_a_supported_website(api, test_users, db_session):
    owner, _ = test_users
    payload = apartment_payload(
        craiova_id(db_session),
        input_source="listing_url",
        source={"url": "https://attacker.example/listing", "observed_at": "2026-11-25T10:00:00Z"},
    )

    assert api(owner).post("/analyses", json=payload).status_code == 422
