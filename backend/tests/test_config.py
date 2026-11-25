import pytest

from app.core.config import Settings

PSYCOPG_URL = "postgresql+psycopg://user:secret@db.example.com:5432/postgres"


@pytest.mark.parametrize(
    "configured_url",
    [
        "postgresql://user:secret@db.example.com:5432/postgres",
        "postgres://user:secret@db.example.com:5432/postgres",
        PSYCOPG_URL,
    ],
)
def test_database_url_uses_psycopg_driver(configured_url):
    settings = Settings(_env_file=None, database_url=configured_url)

    assert settings.database_url == PSYCOPG_URL


@pytest.mark.parametrize("configured_url", [None, "", "   "])
def test_missing_database_url_is_none(configured_url):
    settings = Settings(_env_file=None, database_url=configured_url)

    assert settings.database_url is None
