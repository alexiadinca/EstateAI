"""Verification of Supabase Auth access tokens.

Supabase signs access tokens with an asymmetric key and publishes the matching public keys
at <project>/auth/v1/.well-known/jwks.json. The backend therefore needs only the project URL,
never a secret key, to check that a token was issued by this Supabase project.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import jwt

# Only asymmetric algorithms are accepted. Allowing a shared-secret algorithm such as HS256
# would let anyone who obtains a public key forge tokens (algorithm confusion attack).
ACCEPTED_ALGORITHMS = ["ES256", "RS256"]

# Supabase issues tokens with this audience and role for signed-in users.
SUPABASE_AUDIENCE = "authenticated"
AUTHENTICATED_ROLE = "authenticated"

# Small tolerance for clock differences between Supabase and this server.
CLOCK_SKEW_SECONDS = 10

SigningKeyResolver = Callable[[str], Any]


class InvalidTokenError(Exception):
    """The access token is missing claims, expired, or not signed by this Supabase project."""


class AuthServiceUnavailableError(Exception):
    """The public signing keys could not be downloaded from Supabase."""


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identity extracted from a verified access token."""

    user_id: uuid.UUID
    email: str
    first_name: str | None
    last_name: str | None


class SupabaseTokenVerifier:
    def __init__(self, issuer: str, signing_key_resolver: SigningKeyResolver) -> None:
        self._issuer = issuer
        self._resolve_signing_key = signing_key_resolver

    @classmethod
    def for_project(cls, supabase_url: str) -> "SupabaseTokenVerifier":
        """Create a verifier that downloads and caches the project's public signing keys."""
        auth_url = supabase_url.rstrip("/") + "/auth/v1"
        jwks_client = jwt.PyJWKClient(
            f"{auth_url}/.well-known/jwks.json", cache_keys=True, lifespan=600, timeout=10
        )

        def resolve_signing_key(token: str) -> Any:
            try:
                return jwks_client.get_signing_key_from_jwt(token).key
            except jwt.PyJWKClientConnectionError as error:
                raise AuthServiceUnavailableError("Could not download signing keys.") from error
            except jwt.PyJWKClientError as error:
                # The token refers to a key this project does not publish.
                raise InvalidTokenError("Unknown signing key.") from error

        return cls(issuer=auth_url, signing_key_resolver=resolve_signing_key)

    def verify(self, token: str) -> AuthenticatedUser:
        """Return the user identified by a valid token, or raise InvalidTokenError."""
        try:
            signing_key = self._resolve_signing_key(token)
            claims = jwt.decode(
                token,
                key=signing_key,
                algorithms=ACCEPTED_ALGORITHMS,
                audience=SUPABASE_AUDIENCE,
                issuer=self._issuer,
                leeway=CLOCK_SKEW_SECONDS,
                options={"require": ["exp", "iat", "sub", "aud", "iss"]},
            )
        except jwt.PyJWTError as error:
            raise InvalidTokenError(f"Token rejected: {type(error).__name__}.") from error

        if claims.get("role") != AUTHENTICATED_ROLE:
            raise InvalidTokenError("Token does not belong to a signed-in user.")

        try:
            user_id = uuid.UUID(claims["sub"])
        except ValueError as error:
            raise InvalidTokenError("Token subject is not a user id.") from error

        email = (claims.get("email") or "").strip()
        if not email:
            # EstateAI accounts are email-based; anonymous sessions have no email.
            raise InvalidTokenError("Token has no email address.")

        # Names entered at registration are stored by Supabase in user_metadata.
        user_metadata = claims.get("user_metadata") or {}
        return AuthenticatedUser(
            user_id=user_id,
            email=email,
            first_name=_optional_text(user_metadata.get("first_name")),
            last_name=_optional_text(user_metadata.get("last_name")),
        )


def _optional_text(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()
