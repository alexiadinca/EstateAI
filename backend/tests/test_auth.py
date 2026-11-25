"""Tests for access token verification and the authenticated /me endpoint.

Tokens are signed with a key pair generated for the test run, so no Supabase project,
network access or database is needed.
"""

import time
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.api.routes import users as users_routes
from app.auth.dependencies import get_token_verifier
from app.auth.token_verifier import InvalidTokenError, SupabaseTokenVerifier
from app.db.session import get_db_session
from app.main import app

ISSUER = "https://test-project.supabase.co/auth/v1"
USER_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")

SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())
OTHER_SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())


def make_token(signing_key=SIGNING_KEY, algorithm="ES256", **claim_overrides) -> str:
    now = int(time.time())
    claims = {
        "sub": str(USER_ID),
        "email": "demo1@example.com",
        "role": "authenticated",
        "aud": "authenticated",
        "iss": ISSUER,
        "iat": now,
        "exp": now + 3600,
        "user_metadata": {"first_name": "Ana", "last_name": "Popescu"},
    }
    claims.update(claim_overrides)
    claims = {name: value for name, value in claims.items() if value is not None}
    return jwt.encode(claims, signing_key, algorithm=algorithm)


@pytest.fixture
def verifier() -> SupabaseTokenVerifier:
    public_key = SIGNING_KEY.public_key()
    return SupabaseTokenVerifier(issuer=ISSUER, signing_key_resolver=lambda token: public_key)


def test_valid_token_returns_user_identity(verifier):
    user = verifier.verify(make_token())

    assert user.user_id == USER_ID
    assert user.email == "demo1@example.com"
    assert user.first_name == "Ana"
    assert user.last_name == "Popescu"


def test_missing_names_stay_unknown(verifier):
    user = verifier.verify(make_token(user_metadata={"first_name": "  "}))

    assert user.first_name is None
    assert user.last_name is None


@pytest.mark.parametrize(
    "description, token",
    [
        ("expired", make_token(iat=int(time.time()) - 7200, exp=int(time.time()) - 3600)),
        ("signed by another key", make_token(signing_key=OTHER_SIGNING_KEY)),
        ("wrong audience", make_token(aud="other-service")),
        ("wrong issuer", make_token(iss="https://another-project.supabase.co/auth/v1")),
        ("anonymous role", make_token(role="anon")),
        ("no email", make_token(email=None)),
        ("subject is not a user id", make_token(sub="not-a-uuid")),
        ("no expiry", make_token(exp=None)),
        (
            "shared-secret algorithm",
            make_token(signing_key="a-forged-shared-secret-of-32-bytes", algorithm="HS256"),
        ),
    ],
)
def test_invalid_tokens_are_rejected(verifier, description, token):
    with pytest.raises(InvalidTokenError):
        verifier.verify(token)


@pytest.fixture
def client(verifier, monkeypatch):
    """API client whose token checks use the test key and whose profile storage is faked."""

    def fake_get_or_create_profile(session, user):
        return SimpleNamespace(
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role="user",
            registered_at=datetime(2026, 11, 25, tzinfo=UTC),
        )

    monkeypatch.setattr(users_routes, "get_or_create_profile", fake_get_or_create_profile)
    app.dependency_overrides[get_token_verifier] = lambda: verifier
    app.dependency_overrides[get_db_session] = lambda: None
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_me_requires_a_token(client):
    response = client.get("/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_rejects_an_invalid_token(client):
    token = make_token(signing_key=OTHER_SIGNING_KEY)

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_me_returns_the_profile_of_the_token_owner(client):
    response = client.get("/me", headers={"Authorization": f"Bearer {make_token()}"})

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == str(USER_ID)
    assert body["email"] == "demo1@example.com"
    assert body["first_name"] == "Ana"
